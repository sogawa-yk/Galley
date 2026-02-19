# 設計書

## アーキテクチャ概要

既存の配布用Terraform + Dockerイメージのデプロイパイプラインに対する修正。アーキテクチャ自体の変更はなく、各コンポーネントの設定不備を修正する。

```
MCPクライアント → API Gateway (HTTPS) → Container Instance (HTTP:8000/mcp)
                   ↓ token検証                  ↓ ヘルスチェック
                   クエリパラメータ存在チェック       GET /health → 200 OK
```

## コンポーネント設計

### 1. Terraform変数・出力（deploy/）

**修正内容**:
- `variables.tf`: `galley_image_url`のデフォルト値を空文字に変更（`container-instance.tf`のフォールバックロジックで自動生成）
- `variables.tf`: 未使用の`dynamic_group_id`変数を削除
- `iam.tf`: 全コメントアウト済みファイルを削除
- `outputs.tf`: `nonsensitive()`関数でrandom_passwordの値をアンラップ

**実装の要点**:
- Terraformでは`variable`の`default`値に他の`var.*`を参照できない
- `random_password.result`はTerraformが自動的にsensitive扱いする。`sensitive = true`を外すだけではエラーになり、`nonsensitive()`で明示的にアンラップが必要

### 2. Dockerfile（docker/Dockerfile）

**修正内容**:
- `uv sync --frozen --no-dev` → `uv sync --frozen --no-dev --no-editable`
- OCI CLIインストールを`pip`から`uv`に変更

**実装の要点**:
- `uv sync`はデフォルトでeditableインストール。`.venv/`内には`/build/src/`へのシンボリックリンク（`.pth`ファイル）しか作られない
- マルチステージビルドのランタイムステージには`/build/src/`が存在しないため、`--no-editable`でsite-packagesに実体をコピーする必要がある

### 3. MCPサーバー（src/galley/）

**修正内容**:
- `__main__.py`: `mcp.run()` → `mcp.run(transport="streamable-http", host=config.host, port=config.port)`
- `server.py`: `@mcp.custom_route("/health", methods=["GET"])`でヘルスチェックエンドポイントを追加

**実装の要点**:
- FastMCP 2.xの`mcp.run()`はデフォルトで`stdio`トランスポート。HTTPアクセスには`streamable-http`を明示指定
- `streamable-http`モードでは`/mcp`パスのみが自動的に登録され、`/health`等のカスタムパスは提供されない
- Container Instanceのヘルスチェック（`GET /health`）が404を返すとコンテナが再起動ループに入る

## データフロー

### MCPクライアント接続フロー
```
1. クライアント → API Gateway: POST /mcp?token=xxx
2. API Gateway: tokenクエリパラメータの存在を検証（ENFORCING）
3. API Gateway → Container Instance: POST http://<private_ip>:8000/mcp
4. FastMCP: Streamable HTTP でJSONRPCリクエストを処理
5. Container Instance → API Gateway → クライアント: SSEレスポンス
```

### ヘルスチェックフロー
```
1. Container Instance Runtime: GET http://localhost:8000/health (30秒間隔)
2. FastMCP custom_route: JSONResponse({"status": "ok"})
3. HTTP 200 → ヘルスチェック成功
```

## テスト戦略

### ローカル検証
- Dockerイメージをローカルビルド→コンテナ起動→curl で `/health` と `/mcp` を検証
- MCP `initialize` リクエストに正常応答が返ることを確認
- MCP `tools/list` で15個のツールが返却されることを確認

### リモート検証
- API Gateway経由で同様のリクエストを送信し、502ではなく正常応答を確認
- MCPクライアント（Claude Desktop）からの接続テスト

## 変更ファイル一覧

```
deploy/variables.tf      # galley_image_urlデフォルト値修正、dynamic_group_id削除
deploy/iam.tf            # 削除
deploy/outputs.tf        # nonsensitive()追加
docker/Dockerfile        # --no-editable追加、uv化
src/galley/__main__.py   # streamable-httpトランスポート指定
src/galley/server.py     # /healthエンドポイント追加
.gitignore               # node_modules/追加
```

## 実装の順序

1. Terraform修正（variables.tf, iam.tf削除, outputs.tf）
2. Dockerfile修正（--no-editable）
3. MCPサーバー修正（トランスポート変更、ヘルスチェック追加）
4. ローカルでのDockerビルド・テスト
5. OCIRへのイメージプッシュ
6. Resource Managerで再デプロイ
7. リモート接続テスト

---

## 追加設計: Claude Desktop接続問題の修正（2026-02-18追記）

### 問題の分析

**症状**: Claude Desktopで `https://xxx/mcp?token=xxx` を入力すると「There was an error connecting to the MCP server. Please check your server URL and make sure your server handles auth correctly.」エラーが発生。curlでは全エンドポイント正常動作。

**調査結果**:
- `GET /health?token=xxx` → 200 OK ✅
- `POST /mcp?token=xxx` (initialize) → 200 OK、protocolVersion=2025-03-26 ✅
- `POST /mcp?token=xxx` (tools/list) → 15ツール返却 ✅
- `POST /mcp`（tokenなし） → 400 "Missing required parameters 'token'"
- `GET /.well-known/oauth-authorization-server?token=xxx` → 404 Not Found
- `OPTIONS /mcp?token=xxx` → 405 Method Not Allowed

**根本原因仮説**:
Claude Desktopの StreamableHTTP接続フローでは、初期ハンドシェイク時にtokenクエリパラメータなしのリクエスト（OAuth discovery、初期GET等）を送信する可能性がある。API Gatewayの `query_parameter_validations` が `ENFORCING` モードのため、これらのリクエストが400エラーで拒否される。

参考: [Claude Desktop既知バグ #11814](https://github.com/anthropics/claude-code/issues/11814) - カスタムOAuth MCP接続が機能しない問題

### 修正設計

**方針**: API Gatewayのtoken検証を緩和し、アプリケーション側で適切なtoken検証を実装する。

#### 1. API Gateway変更（`deploy/api-gateway.tf`）

```hcl
# 変更前
query_parameter_validations {
  parameters {
    name     = "token"
    required = true
  }
  validation_mode = "ENFORCING"
}

# 変更後
query_parameter_validations {
  parameters {
    name     = "token"
    required = true
  }
  validation_mode = "PERMISSIVE"  # ログのみ、ブロックしない
}
```

#### 2. アプリケーション側token検証（`src/galley/server.py`）

FastMCPの `custom_route` を使用して、`/mcp` パスへのリクエストにtoken検証を追加:

```python
# MCPリクエストのtoken検証
# - GALLEY_URL_TOKEN環境変数が設定されている場合のみ検証
# - tokenクエリパラメータとGALLEY_URL_TOKENが一致しない場合は401
# - /healthパスはtoken検証をスキップ（Container Instanceヘルスチェック用）
```

**実装の要点**:
- FastMCPの `streamable-http` モードでは、`/mcp` エンドポイントはFastMCP内部で処理される
- `custom_route` ではなく、ASGIミドルウェアまたはFastMCPのauth機能を使用する必要がある
- FastMCPの `auth` パラメータを調査し、最適な実装方法を決定する

#### 3. テスト計画

**自動テスト（pytest）**:
- 既存unit/integration tests → 既存機能の回帰テスト

**ローカルDocker curlテスト**:
- `POST /mcp`（正しいtoken）→ 200 OK
- `POST /mcp`（不正token）→ 401 Unauthorized
- `POST /mcp`（tokenなし）→ 401 Unauthorized
- `GET /health`（tokenなし）→ 200 OK

**リモートcurlテスト**:
- API Gateway経由で上記と同様のパターンを検証
- MCP full flow（initialize → initialized → tools/list）

**ユーザー実施**:
- Claude Desktopからの接続テスト

### 追加変更ファイル

```
deploy/api-gateway.tf    # validation_mode: ENFORCING → PERMISSIVE
src/galley/server.py     # token検証ミドルウェア追加
src/galley/config.py     # GALLEY_URL_TOKEN設定追加（必要に応じて）
```
