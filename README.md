# Galley - OCI プリセールス支援 MCP サーバー

AI駆動のOCIソリューション構築プラットフォーム。Claude等のLLMからMCP (Model Context Protocol) 経由でOCIリソースの設計・構築・デプロイを一貫して実行できます。

## Deploy to Oracle Cloud

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?region=home&zipUrl=https://github.com/sogawa-yk/Galley/releases/latest/download/galley-stack.zip)

> ボタンをクリックするとOCI Console の Resource Manager スタック作成画面が開きます。

### 前提条件

デプロイ前に以下を準備してください:

1. **OCI テナンシー** — 有効なOCIアカウント
2. **コンパートメント** — Galleyインフラを配置するコンパートメント
3. **VCN + サブネット** — 既存のVCNにパブリックサブネット（API Gateway用）とプライベートサブネット（Container Instance用）が必要
4. **コンテナイメージ** — GalleyイメージがOCIRにpush済みであること

### コンテナイメージの準備

```bash
# ビルド
docker build -f docker/Dockerfile -t galley .

# タグ付け（リージョンとネームスペースを置き換えてください）
docker tag galley <region>.ocir.io/<namespace>/galley:latest

# OCIRにpush
docker push <region>.ocir.io/<namespace>/galley:latest
```

### Terraform 入力変数

| 変数 | 必須 | デフォルト | 説明 |
|------|------|-----------|------|
| `compartment_ocid` | Yes | - | インフラ配置コンパートメントOCID |
| `region` | Yes | - | OCIリージョン (例: `ap-tokyo-1`) |
| `vcn_id` | Yes | - | 既存VCNのOCID |
| `public_subnet_id` | Yes | - | パブリックサブネットOCID (API Gateway配置先) |
| `private_subnet_id` | Yes | - | プライベートサブネットOCID (Container Instance配置先) |
| `galley_work_compartment_id` | No | `compartment_ocid` | Galleyの作業対象コンパートメント |
| `image_tag` | No | `latest` | コンテナイメージタグ |
| `galley_image_url` | No | 自動生成 | イメージフルURL (OCIR自動構成を上書き) |
| `container_instance_shape` | No | `CI.Standard.E4.Flex` | Container Instanceシェイプ |
| `container_instance_ocpus` | No | `1` | OCPU数 |
| `container_instance_memory_in_gbs` | No | `2` | メモリ (GB) |

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

- **ヒアリング**: 対話的な要件ヒアリングで顧客の要件を構造化
- **アーキテクチャ設計**: ヒアリング結果からOCIサービスの最適な組み合わせを設計
- **バリデーション**: OCI固有の制約に基づく構成検証
- **IaC生成**: Terraformコードの自動生成
- **インフラ構築**: Terraform plan/apply の自動実行・エラー修正ループ
- **アプリケーションデプロイ**: テンプレートからのアプリ生成・カスタマイズ・デプロイ

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
| Terraform | IaC実行 (コンテナ内同梱) |

## ライセンス

TBD
