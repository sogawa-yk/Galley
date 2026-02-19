# 要求内容

## 概要

OCI Resource Managerを使ったGalley MCPサーバーのデプロイで発生した複数の問題を修正し、MCPクライアントからリモートエンドポイントへ正常に接続できる状態にする。

## 背景

20260217-distribution-terraformで作成したDockerfile・Terraform一式をOCI Resource Managerでデプロイしたところ、以下の問題が連鎖的に発生し、MCPクライアント（Claude Desktop等）からの接続ができなかった:

1. Terraform applyエラー（変数デフォルト値での変数参照）
2. コンテナ起動エラー（Pythonモジュール解決失敗）
3. MCPトランスポートの不一致（stdio vs HTTP）
4. ヘルスチェック失敗によるコンテナ再起動ループ
5. Terraform出力のsensitiveフラグによるトークン非表示

## 実装対象の機能

### 1. Terraform変数・出力の修正
- `variables.tf`の`galley_image_url`デフォルト値で`${var.image_tag}`を参照していたエラーを修正
- 未使用の`iam.tf`（全コメントアウト済み）と`dynamic_group_id`変数を削除
- `outputs.tf`の`sensitive`フラグを`nonsensitive()`でアンラップし、Resource ManagerでURLトークンを表示可能に

### 2. Dockerfileのビルド修正
- `uv sync`に`--no-editable`を追加し、ランタイムステージでモジュールが解決できるように修正
- OCI CLIインストールを`pip`から`uv`に変更

### 3. MCPサーバーのHTTP対応
- `mcp.run()`のトランスポートを`stdio`から`streamable-http`に変更
- `custom_route`で`/health`エンドポイントを追加し、Container Instanceのヘルスチェックに対応

### 4. リポジトリ整備
- `.gitignore`に`node_modules/`を追加
- ステージングされていた大量の`node_modules/`ファイルを除外

## 受け入れ条件

### Terraformデプロイ
- [x] `terraform apply`がエラーなく完了する
- [x] `mcp_endpoint_url`と`url_token`がOutputsに平文で表示される

### コンテナ起動
- [x] コンテナが`No module named galley`エラーなく起動する
- [x] `streamable-http`トランスポートで`/mcp`エンドポイントがリッスンする
- [x] `/health`エンドポイントが`200 OK`を返し、ヘルスチェックが成功する

### MCP接続
- [x] リモートエンドポイント(`/mcp?token=...`)にPOSTで`initialize`リクエストを送信し、正常応答を得る
- [x] MCPクライアント（Claude Desktop等）からリモートエンドポイントに接続できる

## 成功指標

- MCPクライアントからリモートエンドポイント経由で`tools/list`が取得できる

## スコープ外

以下はこのフェーズでは実装しない:

- ~~URLトークンのアプリケーション側検証~~ → Claude Desktop接続のため必要となり実装済み
- OCI Object Storageとの接続テスト
- MCPツールの機能テスト

## 参照ドキュメント

- `.steering/20260217-distribution-terraform/` - 配布用Terraform作成の元タスク
- `docs/architecture.md` - アーキテクチャ設計書
