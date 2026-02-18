# 要求内容

## 概要

Galley MCPサーバーの配布用コンテナイメージ（Dockerfile）と、利用者がOCI環境にGalleyをデプロイするための配布用Terraformファイル群を作成する。

## 背景

Phase 1でMCPサーバー基盤とヒアリング機能が実装済みだが、利用者がGalleyを実際のOCI環境にデプロイする手段がない。利用者が`terraform apply`一発でGalley環境を構築できるようにするため、コンテナイメージとインフラ定義が必要である。

## 実装対象の機能

### 1. Dockerfile（コンテナイメージ定義）

- Python 3.12+、OCI CLI、OCI SDK for Python、Terraform + OCI Provider、kubectlを含むコンテナイメージを定義
- Galleyアプリケーション（`src/galley/`）をパッケージとしてインストール
- FastMCPのSSE/StreamableHTTPでリッスンするエントリポイントを設定
- マルチステージビルドでイメージサイズを最適化

### 2. 配布用Terraformファイル（`deploy/`）

- 利用者が`terraform apply`で以下のOCIリソースを自動作成できるTerraformコードを提供:
  - VCN、パブリック/プライベートサブネット、Security List、NAT Gateway、Internet Gateway、Service Gateway
  - API Gateway（HTTPS終端 + URLトークン認証）
  - Container Instance（Galleyコンテナ実行環境）
  - Object Storage バケット（セッションデータ等の永続化）
  - Dynamic Group + IAM Policy（Resource Principal認証）
- 利用者が入力する変数は最小限（`compartment_id`、`region`、`galley_work_compartment_id`（任意）、`image_tag`（任意））
- `terraform apply`完了後、MCP接続用のURLトークン付きエンドポイントをoutputとして出力

## 受け入れ条件

### Dockerfile
- [ ] `docker/Dockerfile`が存在し、`docker build`でビルドできる
- [ ] コンテナイメージにPython 3.12+、OCI CLI、Terraform、kubectlが含まれる
- [ ] Galleyアプリケーションがインストールされ、MCPサーバーとして起動できる

### 配布用Terraform
- [ ] `deploy/`ディレクトリに必要なTerraformファイルが存在する
- [ ] `terraform init && terraform validate`がエラーなく通る
- [ ] 入力変数は`compartment_id`、`region`、`galley_work_compartment_id`（任意）、`image_tag`（任意）のみ
- [ ] outputにMCPエンドポイントURL（URLトークン付き）が含まれる
- [ ] API GatewayがHTTPS終端とURLトークン認証を提供する構成である
- [ ] Container Instanceがプライベートサブネットに配置される構成である
- [ ] Dynamic GroupとIAM Policyが最小権限原則に従っている

### 品質チェック
- [ ] 既存テストが全てパスする（`uv run pytest`）
- [ ] リントエラーがない（`uv run ruff check .`）
- [ ] 型エラーがない（`uv run mypy src/`）

## 成功指標

- Dockerfileからコンテナイメージがビルドできる
- 配布用Terraformが`terraform validate`に通る
- 既存のMCPサーバー機能に影響を与えない

## スコープ外

以下はこのフェーズでは実装しません:

- OCIRへのコンテナイメージの実際のpush（CI/CDパイプラインで対応予定）
- 実際のOCI環境への`terraform apply`実行（OCI環境依存のため手動検証）
- CI/CDパイプラインの構築
- TLS証明書のカスタムドメイン対応
- OAuth認証への移行オプション

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書（F3の受け入れ条件）
- `docs/functional-design.md` - 機能設計書（配布Terraformサービスの設計）
- `docs/architecture.md` - アーキテクチャ設計書（セキュリティアーキテクチャ）
- `docs/repository-structure.md` - リポジトリ構造定義書（deploy/、docker/の配置）
