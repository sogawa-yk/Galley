# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### 実装可能なタスクのみを計画
- 計画段階で「実装可能なタスク」のみをリストアップ
- 「将来やるかもしれないタスク」は含めない
- 「検討中のタスク」は含めない

### タスクスキップが許可される唯一のケース
以下の技術的理由に該当する場合のみスキップ可能:
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

### タスクが大きすぎる場合
- タスクを小さなサブタスクに分割
- 分割したサブタスクをこのファイルに追加
- サブタスクを1つずつ完了させる

---

## フェーズ1: Terraform修正

- [x] `deploy/variables.tf`の`galley_image_url`デフォルト値を修正（`${var.image_tag}`参照を空文字に変更）
- [x] `deploy/iam.tf`を削除（全コメントアウト済み、未使用）
- [x] `deploy/variables.tf`から`dynamic_group_id`変数を削除
- [x] `deploy/outputs.tf`の`mcp_endpoint_url`と`url_token`に`nonsensitive()`を適用
- [x] gitプッシュ

## フェーズ2: Dockerfile修正

- [x] `docker/Dockerfile`のOCI CLIインストールを`pip`から`uv`に変更
- [x] `docker/Dockerfile`の`uv sync`に`--no-editable`フラグを追加
- [x] `.gitignore`に`node_modules/`を追加し、ステージングから除外
- [x] gitプッシュ

## フェーズ3: MCPサーバーHTTP対応

- [x] `src/galley/__main__.py`で`mcp.run(transport="streamable-http")`に変更
- [x] `src/galley/server.py`に`/health`エンドポイントを追加（`@mcp.custom_route`）
- [x] gitプッシュ

## フェーズ4: ローカル検証

- [x] Dockerイメージをローカルビルド
- [x] コンテナ起動し、ログで`transport 'streamable-http'`を確認
- [x] `GET /health` → `200 OK`、`{"status": "ok"}`を確認
- [x] `POST /mcp`（initialize）→ 正常応答を確認
- [x] `POST /mcp`（tools/list）→ 15個のツール返却を確認

## フェーズ5: デプロイとリモート検証

- [x] OCIRにイメージプッシュ（`kix.ocir.io/orasejapan/galley:latest`）
- [x] ~~Resource Managerで再デプロイ（apply）~~（実装方針変更により不要: Container Instanceはイメージ名・タグが同じ場合、再起動だけで新イメージをプルする仕様のため、terraform applyは不要）
- [x] リモートエンドポイントに`GET /health?token=...` → `200 OK`を確認
- [x] リモートエンドポイントに`POST /mcp?token=...`（initialize）→ 正常応答を確認（`mcp-session-id`返却、`protocolVersion: 2025-03-26`確認）
- [x] リモートエンドポイントに`POST /mcp?token=...`（tools/list）→ 15ツール返却を確認
- [ ] MCPクライアント（Claude Desktop）からの接続テスト → **Phase 8で対応**

## フェーズ6: 自動テスト実行

- [x] pytest unit tests実行 → 全テストパス確認（67/67）
- [x] pytest integration tests実行 → MCP protocol経由の全フロー確認（20/20）
- [x] ローカルDockerビルド＆コンテナ起動テスト（curl検証 → 全5パターンパス）

## フェーズ7: Claude Desktop接続問題の調査と修正

**調査結果**: Claude Desktopが「There was an error connecting to the MCP server. Please check your server URL and make sure your server handles auth correctly.」エラーを返す。curlでは全エンドポイント正常動作。

**根本原因仮説**: API Gatewayが全パスに`token`クエリパラメータを要求（ENFORCING）しているため、Claude Desktopの初期ハンドシェイク（OAuth discovery等のtokenなしリクエスト）が400エラーで拒否されている。

**修正方針**: API Gatewayのtoken検証をPERMISSIVE（ログのみ）に変更し、アプリケーション側で`GALLEY_URL_TOKEN`環境変数との一致検証を実装する。

- [x] API Gatewayの`query_parameter_validations`を`ENFORCING`→`PERMISSIVE`に変更
- [x] FastMCPサーバーにtoken検証ミドルウェアを追加（`/health`は除外、`/mcp`は必須）
- [x] tokenなしリクエストへの適切なエラーレスポンス（401 Unauthorized）を実装
- [x] ローカルHTTPサーバーでtoken検証テスト（正しいtoken・不正token・tokenなし → 全パス）
- [x] コミット＆OCIRプッシュ
- [x] Container Instance再起動（Terraform再applyにより再作成→手動restart）
- [x] リモートcurlテスト再実行（health/initialize/tools_list → 全5パターンパス）

## フェーズ8: Claude Desktop接続テスト（ユーザー実施）

- [x] ユーザー: Claude Desktopからリモートエンドポイントに接続テスト → 正常接続確認
- [x] ユーザー: tools/listが取得できることを確認

---

## 実装後の振り返り

### 実装完了日
2026-02-18

### 計画と実績の差分

**計画と異なった点**:
- 当初はTerraformの変数修正のみの想定だったが、デプロイして初めて発覚した問題が複数あり、Dockerfile・アプリケーションコード・Terraform出力と広範囲の修正が必要になった
- `sensitive`フラグを単に外すだけではエラーになり、`nonsensitive()`関数が必要だった（Terraformの`random_password.result`が自動的にsensitive扱いされるため）
- FastMCPの`mcp.run()`デフォルトが`stdio`トランスポートであることが判明し、`streamable-http`を明示指定する必要があった
- FastMCPの`streamable-http`モードには`/health`パスが含まれず、`custom_route`で追加が必要だった
- Claude Desktopからの接続がAPI Gatewayのtoken検証（ENFORCING）によりブロックされていた。API GatewayをPERMISSIVEに変更し、アプリケーション側でtoken検証ミドルウェアを実装することで解決
- 当初スコープ外だったURLトークンのアプリケーション側検証が、Claude Desktop接続のために必要となり実装

**新たに必要になったタスク**:
- `--no-editable`フラグの追加（editable installがマルチステージビルドと非互換）
- `/health`エンドポイントの追加（Container Instanceヘルスチェック対応）
- `nonsensitive()`関数の適用（`sensitive`フラグ削除だけでは不十分）
- API GatewayのENFORCING→PERMISSIVE変更（Claude Desktop初期ハンドシェイク対応）
- TokenAuthMiddlewareの実装（アプリ側token検証）

### 学んだこと

**技術的な学び**:
- `uv sync`はデフォルトでeditableインストール。マルチステージDockerビルドでは必ず`--no-editable`を指定すること
- FastMCP 2.xの`mcp.run()`はデフォルト`stdio`。HTTP公開には`transport="streamable-http"`の明示指定が必須
- FastMCPの`streamable-http`モードは`/mcp`パスのみを提供。ヘルスチェック等は`@mcp.custom_route`で追加
- Terraformの`random_password.result`は自動sensitive。出力には`nonsensitive()`関数でのアンラップが必要
- Terraformの`variable`ブロックの`default`値では他の`var.*`を参照できない
- **Claude DesktopのリモートMCP接続では、初期ハンドシェイク時にtokenなしリクエストが送信される。API Gatewayでのtoken検証（ENFORCING）はこれをブロックするため、token検証はアプリケーション側で行う必要がある**
- FastMCPの`http_app(middleware=[...])`パラメータでStarletteミドルウェアを注入でき、`custom_route`で追加したエンドポイントにも適用される
- Container Instanceは同一イメージ名:タグの場合、再起動で最新イメージをプルする

**プロセス上の改善点**:
- ローカルでDockerコンテナを起動してcurlで検証する手法が、リモートデバッグが困難な場合に非常に有効だった
- 問題が連鎖的に発生するため、1つ修正→ビルド→テストの小さなサイクルで進めるのが効果的
- curlによるMCPプロトコルシミュレーション（initialize → initialized → tools/list）がClaude Desktop不在時の有効なテスト手法

### 次回への改善提案
- Dockerfileのマルチステージビルドでは`uv sync --no-editable`をデフォルトにする
- FastMCPでHTTP公開する場合は、最初から`transport`とヘルスチェックを設定する
- デプロイ前にローカルでコンテナを起動し、全エンドポイントの疎通テストを行うステップを標準化する
- Terraform出力でsensitiveな値を表示する必要がある場合は、最初から`nonsensitive()`を使う
- **リモートMCPサーバーのtoken検証はAPI Gatewayではなくアプリケーション側で実装する（MCPクライアントの初期ハンドシェイク互換性のため）**
- OCIRプッシュ→Terraform apply の順序を守ること（逆になると古いイメージがデプロイされる）
