# Galley - OCI プリセールス支援 MCP サーバー

AI駆動のOCIソリューション構築プラットフォーム。Claude等のLLMからMCP (Model Context Protocol) 経由でOCIリソースの設計・構築・デプロイを一貫して実行できます。

## Deploy to Oracle Cloud

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?region=home&zipUrl=https://github.com/sogawa-yk/Galley/releases/latest/download/galley-stack.zip)

> ボタンをクリックするとOCI Resource Manager のスタック作成画面が開きます。コンテナイメージは GitHub Container Registry (ghcr.io) から自動で取得されるため、事前のイメージビルドやプッシュは不要です。

### 前提条件

1. **OCI テナンシー** - 有効なOCIアカウント
2. **コンパートメント** - Galleyインフラを配置するコンパートメント

### デプロイされるリソース

| リソース | 用途 |
|---------|------|
| VCN + サブネット + ゲートウェイ | ネットワーク (自動作成) |
| Container Instance | Galleyサーバー実行 |
| API Gateway | HTTPS エンドポイント公開 |
| Object Storage バケット | セッションデータ永続化 |
| Build Instance (Compute) | アプリケーションのDockerビルド用 |
| NSG (Network Security Group) | アクセス制御 |

### Terraform 入力変数

| 変数 | 必須 | デフォルト | 説明 |
|------|------|-----------|------|
| `compartment_ocid` | Yes | - | インフラ配置コンパートメントOCID |
| `region` | Yes | - | OCIリージョン (例: `ap-tokyo-1`) |
| `galley_work_compartment_id` | No | `compartment_ocid` | Galleyが操作するリソースの配置先コンパートメント |
| `vcn_cidr` | No | `10.0.0.0/16` | VCNのCIDRブロック |
| `galley_image_url` | No | `ghcr.io/sogawa-yk/galley:latest` | コンテナイメージのフルURL |
| `container_instance_shape` | No | `CI.Standard.E4.Flex` | Container Instanceシェイプ |
| `container_instance_ocpus` | No | `1` | Container Instance OCPU数 |
| `container_instance_memory_in_gbs` | No | `2` | Container Instance メモリ (GB) |
| `build_instance_shape` | No | `VM.Standard.E4.Flex` | Build Instanceシェイプ |
| `build_instance_ocpus` | No | `1` | Build Instance OCPU数 |
| `build_instance_memory_in_gbs` | No | `8` | Build Instance メモリ (GB) |
| `ocir_username` | No | `""` | OCIR認証ユーザー名 (アプリビルド時に使用) |
| `ocir_auth_token` | No | `""` | OCIR認証トークン (sensitive) |

> `tenancy_ocid` は Resource Manager が自動注入するため指定不要です。

### デプロイ後の利用方法

1. Resource Manager の **出力** タブから `mcp_endpoint_url` を確認
2. Claude Desktop の MCP 設定に追加:

```json
{
  "mcpServers": {
    "galley": {
      "url": "<mcp_endpoint_url の値>"
    }
  }
}
```

3. Claude Desktop を再起動し、Galley のツールが利用可能になったことを確認

## 機能

- **ヒアリング** - 対話的な要件ヒアリングで顧客の要件を構造化
- **アーキテクチャ設計** - ヒアリング結果からOCIサービスの最適な組み合わせを設計
- **バリデーション** - OCI固有の制約に基づく構成検証
- **IaC生成** - Terraformコードの自動生成
- **インフラ構築** - Resource Manager経由のTerraform plan/apply 実行
- **アプリデプロイ** - テンプレートからのアプリ生成・カスタマイズ・OKEデプロイ

## 開発

### セットアップ

```bash
# 依存関係のインストール
uv sync

# テスト実行
uv run pytest

# リンター・フォーマッター
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/

# ローカルサーバー起動
uv run python -m galley
```

### テクノロジースタック

| 技術 | 用途 |
|------|------|
| Python 3.12+ | ランタイム |
| FastMCP | MCPサーバーフレームワーク |
| uv | パッケージ管理 |
| OCI SDK for Python | OCI API アクセス |
| Terraform 1.9.8 | IaC実行 (コンテナ内同梱) |
| kubectl 1.30.7 | OKEクラスタ操作 (コンテナ内同梱) |

### リリース

`v*` タグをプッシュすると GitHub Actions が自動実行:

- **publish-image** - ghcr.io へコンテナイメージをビルド・プッシュ (amd64/arm64)
- **package-deploy-stack** - `deploy/` を zip 化し GitHub Release にアップロード

## ライセンス

TBD
