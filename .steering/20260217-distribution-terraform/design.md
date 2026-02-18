# 設計書

## アーキテクチャ概要

F3はGalley MCPサーバーの機能ではなく、利用者がGalley環境をOCI上に構築するためのインフラ定義を提供する。コンテナイメージ定義（Dockerfile）と配布用Terraformファイル群の2つの成果物を作成する。

```
利用者の環境
  │
  │ 1. docker build（開発時）/ OCIR pull（本番）
  │ 2. cd deploy/ && terraform apply
  │
  ▼
┌──────────────────────────────────────────────────┐
│ OCI                                              │
│                                                  │
│  ┌─────────────────────────────────────────┐     │
│  │ VCN (10.0.0.0/16)                       │     │
│  │                                         │     │
│  │  ┌──────────────────────┐               │     │
│  │  │ Public Subnet        │               │     │
│  │  │ (10.0.1.0/24)        │               │     │
│  │  │                      │               │     │
│  │  │  ┌────────────────┐  │               │     │
│  │  │  │ API Gateway    │  │               │     │
│  │  │  │ (HTTPS + Token)│  │               │     │
│  │  │  └───────┬────────┘  │               │     │
│  │  └──────────┼───────────┘               │     │
│  │             │                           │     │
│  │  ┌──────────┼───────────┐               │     │
│  │  │ Private Subnet       │               │     │
│  │  │ (10.0.2.0/24)        │               │     │
│  │  │          │           │               │     │
│  │  │  ┌──────▼────────┐   │               │     │
│  │  │  │ Container     │   │               │     │
│  │  │  │ Instance      │   │               │     │
│  │  │  │ (Galley MCP)  │   │               │     │
│  │  │  └───────────────┘   │               │     │
│  │  └──────────────────────┘               │     │
│  └─────────────────────────────────────────┘     │
│                                                  │
│  ┌─────────────┐  ┌─────────────┐               │
│  │ Object      │  │ Dynamic     │               │
│  │ Storage     │  │ Group +     │               │
│  │ (galley-*)  │  │ IAM Policy  │               │
│  └─────────────┘  └─────────────┘               │
└──────────────────────────────────────────────────┘
```

## コンポーネント設計

### 1. Dockerfile (`docker/Dockerfile`)

**責務**:
- Galleyアプリケーションを含むコンテナイメージの定義
- Python 3.12+、OCI CLI、Terraform、kubectlの同梱

**実装の要点**:
- マルチステージビルドでイメージサイズを最適化
  - ステージ1（builder）: Python依存関係のインストールとパッケージビルド
  - ステージ2（runtime）: OCI CLI、Terraform、kubectlのインストールとアプリケーション配置
- ベースイメージ: `python:3.12-slim`（Debian bookworm slim）
- uvを使用してPython依存関係をインストール
- 非rootユーザーで実行
- ヘルスチェックの定義
- エントリポイント: `python -m galley`

**同梱ツールのインストール方法**:
- OCI CLI: pip経由でインストール（`oci-cli`パッケージ）
- Terraform: HashiCorpの公式リリースからバイナリをダウンロード
- kubectl: Kubernetesの公式リリースからバイナリをダウンロード

### 2. メインTerraform設定 (`deploy/main.tf`)

**責務**:
- OCI Terraform Providerの設定
- Terraformバージョン制約の定義

**実装の要点**:
- `oci` providerの設定（region変数を使用）
- `random` providerの設定（URLトークン生成用）
- 認証はTerraform実行環境のOCI CLI設定に委任

### 3. 変数定義 (`deploy/variables.tf`)

**責務**:
- 利用者が設定する入力変数の定義

**実装の要点**:
- `compartment_id`（必須）: Galleyインフラを配置するコンパートメント
- `region`（必須）: OCIリージョン
- `dynamic_group_id`（必須）: 既存の動的グループOCID（Resource Principal認証用）
- `galley_work_compartment_id`（任意）: Galleyの作業対象コンパートメント（デフォルト: `compartment_id`と同じ）
- `image_tag`（任意）: コンテナイメージのタグ（デフォルト: `latest`）
- `galley_image_url`（任意）: コンテナイメージのフルURL（OCIR URL）

### 4. 出力定義 (`deploy/outputs.tf`)

**責務**:
- `terraform apply`完了後に利用者に必要な情報を出力

**実装の要点**:
- `mcp_endpoint_url`: API GatewayのエンドポイントURL（URLトークン含む）
- `api_gateway_hostname`: API Gatewayのホスト名
- `url_token`: 生成されたURLトークン（sensitive）
- `object_storage_bucket`: 作成されたObject Storageバケット名
- `container_instance_id`: Container InstanceのOCID

### 5. ネットワーク定義 (`deploy/network.tf`)

**責務**:
- VCN、サブネット、ゲートウェイ、セキュリティリスト等のネットワーク構成

**実装の要点**:
- VCN: `10.0.0.0/16`
- パブリックサブネット（`10.0.1.0/24`）: API Gateway用
- プライベートサブネット（`10.0.2.0/24`）: Container Instance用
- Internet Gateway: パブリックサブネット用
- NAT Gateway: プライベートサブネットからの外部アクセス用（Terraform、OCI CLI用）
- Service Gateway: OCIサービスへの内部アクセス用（Object Storage等）
- セキュリティリスト:
  - パブリック: HTTPS（443）のインバウンドを許可
  - プライベート: パブリックサブネットからの8000番ポートインバウンドを許可、アウトバウンドは全許可

### 6. API Gateway定義 (`deploy/api-gateway.tf`)

**責務**:
- HTTPS終端とURLトークン認証の提供

**実装の要点**:
- `oci_apigateway_gateway`: パブリックサブネットに配置
- `oci_apigateway_deployment`: MCPエンドポイントのルーティング
  - パス: `/{path*}`（全パスをバックエンドに転送）
  - バックエンド: Container InstanceのプライベートIPアドレス:8000
  - クエリパラメータ検証: `token`パラメータの存在チェック（API Gateway側）
  - トークン値の一致検証: Galleyアプリケーション側で`GALLEY_URL_TOKEN`環境変数と比較
  - OCI API GatewayのTOKEN_AUTHENTICATIONはJWT形式を前提とするため、単純文字列トークンには不適合。カスタムAuthorizer Function不要の2段構成を採用。
- `random_password`: URLトークンの自動生成（32文字）

### 7. Container Instance定義 (`deploy/container-instance.tf`)

**責務**:
- Galley MCPサーバーの実行環境

**実装の要点**:
- `oci_container_instances_container_instance`: プライベートサブネットに配置
- シェイプ: `CI.Standard.E4.Flex`（1 OCPU / 2GB RAM）
- コンテナ定義:
  - イメージ: `galley_image_url`変数（デフォルト: OCIRパブリックリポジトリ）
  - ポート: 8000
  - 環境変数: `GALLEY_DATA_DIR`、`GALLEY_HOST`、`GALLEY_PORT`
  - ヘルスチェック: HTTPヘルスチェック

### 8. Object Storage定義 (`deploy/object-storage.tf`)

**責務**:
- セッションデータ、Terraform state、テンプレート、バリデーションルールの永続化ストレージ

**実装の要点**:
- `oci_objectstorage_bucket`: バケット作成
- バケット名: `galley-<random_suffix>`（グローバル一意性のため）
- バージョニング有効化（Terraform stateの保護）
- ストレージ層: Standard

### 9. IAM定義 (`deploy/iam.tf`)

**責務**:
- Container InstanceのResource Principal認証に必要なIAM Policy（動的グループは利用者が事前作成済み）

**実装の要点**:
- 動的グループは作成しない（利用者が事前に保有する既存の動的グループOCIDを`var.dynamic_group_id`で受け取る）
- `oci_identity_policy`: コンパートメントレベルで最小権限原則に従った権限付与
  - IAM PolicyのステートメントではOCID参照構文（`dynamic-group id <ocid>`）を使用
  - Object Storage: galleyバケットへの管理権限
  - Resource Manager: `galley_work_compartment_id`内でのスタック管理
  - VCN/Subnet: `galley_work_compartment_id`内でのネットワーク管理
  - Compute: `galley_work_compartment_id`内でのインスタンス管理
  - Container Instances: 読み取り権限

## データフロー

### 利用者によるデプロイフロー
```
1. 利用者がdeploy/ディレクトリで terraform init を実行
2. terraform.tfvars に compartment_id, region, dynamic_group_id を設定
3. terraform apply を実行
4. OCI上にVCN、API Gateway、Container Instance、Object Storage、IAMが作成される
5. URLトークンが自動生成される
6. terraform output でMCPエンドポイントURLを取得
7. MCPホスト（Claude Desktop等）にエンドポイントURLを設定
```

## エラーハンドリング戦略

F3はインフラ定義であり、Pythonコードのエラーハンドリングは不要。Terraform側のエラーハンドリング:

- 変数のバリデーション: `validation`ブロックでOCIDフォーマットの検証
- リソース依存関係: `depends_on`で明示的な依存関係を定義
- URLトークン: `random_password`で自動生成（衝突リスクなし）

## テスト戦略

### Terraformバリデーション
- `terraform init && terraform validate`でHCL構文エラーを検出
- 変数のバリデーションルールが機能することを確認

### Dockerビルドテスト
- `docker build`でイメージがビルドできることを確認
- 基本的なヘルスチェック（コンテナ起動→レスポンス確認）

### 既存テストの回帰
- `uv run pytest`で既存テストが引き続きパスすることを確認

## 依存ライブラリ

新規のPython依存ライブラリの追加はなし。

Terraform Provider:
- `hashicorp/oci` >= 6.0
- `hashicorp/random` >= 3.0

## ディレクトリ構造

```
galley/
├── docker/
│   └── Dockerfile              # NEW: コンテナイメージ定義
├── deploy/
│   ├── main.tf                 # NEW: プロバイダー設定
│   ├── variables.tf            # NEW: 入力変数定義
│   ├── outputs.tf              # NEW: 出力定義
│   ├── network.tf              # NEW: VCN/Subnet/Gateway
│   ├── api-gateway.tf          # NEW: API Gateway
│   ├── container-instance.tf   # NEW: Container Instance
│   ├── object-storage.tf       # NEW: Object Storage
│   └── iam.tf                  # NEW: Dynamic Group/IAM Policy
├── .gitignore                  # UPDATE: Terraform関連の除外追加
└── (既存ファイルは変更なし)
```

## 実装の順序

1. Dockerfileの作成（docker/Dockerfile）
2. Terraform: main.tf + variables.tf（基盤）
3. Terraform: network.tf（ネットワーク構成）
4. Terraform: object-storage.tf（ストレージ）
5. Terraform: iam.tf（認証・認可）
6. Terraform: container-instance.tf（コンテナ実行環境）
7. Terraform: api-gateway.tf（エンドポイント）
8. Terraform: outputs.tf（出力定義）
9. .gitignoreの更新（Terraform関連追加）
10. terraform validate による構文検証
11. 既存テストの回帰確認

## セキュリティ考慮事項

- **Resource Principal認証**: APIキーをコンテナに保持しない設計
- **URLトークン認証**: `random_password`で32文字のトークンを自動生成。Terraform outputでsensitiveとしてマーク
- **最小権限原則**: IAM Policyで操作対象を`galley_work_compartment_id`に限定
- **ネットワーク分離**: Container Instanceをプライベートサブネットに配置し、API Gateway経由のみアクセス可能
- **非rootユーザー**: Dockerコンテナ内で非rootユーザーとして実行
- **Galleyインフラへのアクセス分離**: Galleyが自身のインフラ（Container Instance、API Gateway等）を操作する権限を持たない

## パフォーマンス考慮事項

- Container Instance: 1 OCPU / 2GB RAMを基本構成（PRDの最小構成に準拠）
- マルチステージビルドでDockerイメージサイズを最適化
- Object StorageのバージョニングはStandard層を使用（コスト最適化）

## 将来の拡張性

- `image_tag`変数によるバージョン管理対応
- `galley_work_compartment_id`による権限分離の柔軟性
- Container Instanceのシェイプ変更による垂直スケーリング対応
- OAuth認証への将来的な移行を見据えたAPI Gateway構成
