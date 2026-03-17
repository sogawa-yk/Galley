# Galley - OCI デモ環境ビルダー

AI駆動のOCIソリューション構築プラットフォーム。Claude Codeの**Skills/Workflows**を通じて、自然言語の要望からOCI上のデモ環境を完全自動で設計・構築・デプロイします。

> **Note**: MCP サーバー版は [`mcp`ブランチ](https://github.com/sogawa-yk/Galley/tree/mcp) を参照してください。本ブランチ (main) は同等の機能を Claude Code Skills/Workflows として再実装したものです。

## 概要

プリセールスエンジニアが「こんなデモ環境がほしい」と伝えるだけで、ヒアリング → IaC生成 → インフラ構築 → アプリ生成 → デプロイ → E2E検証 までをワンストップで実行します。

```
ユーザー: 「FastAPIでタスク管理APIを作りたい。DBはMySQL、OKEにデプロイして」
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Workflow: build-demo-env                           │
│                                                     │
│  1. hearing        → hearing/result.json            │
│  2. generate-terraform → generated/*/terraform/     │
│  3. generate-app   → generated/*/app/               │
│  4. deploy-infra   → stack_outputs.json             │
│  5. deploy-app     → endpoints.json                 │
│  6. verify         → test_results.json              │
└─────────────────────────────────────────────────────┘
    │
    ▼
デプロイ済みデモ環境 + E2Eテスト結果
```

## 前提条件

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) がインストール済み
- OCI CLI が設定済み (`~/.oci/config`)
- Python 3.11+
- Terraform (OCI Resource Manager 経由で実行するためローカルは任意)

## 使い方

### クイックスタート

```bash
# リポジトリをクローン
git clone https://github.com/sogawa-yk/Galley.git
cd Galley

# Claude Code を起動し、ワークフローを実行
claude

# Claude Code 内で:
/workflow build-demo-env
```

ワークフローが起動すると、対話形式でヒアリングが始まります。要望を伝えるだけで、残りは自動で進行します。

### 個別スキルの実行

各スキルは単体でも利用できます:

```
/skill hearing              # ヒアリングのみ実行
/skill generate-terraform   # Terraform コード生成
/skill generate-app         # アプリケーション生成
/skill deploy-infra         # インフラ構築 (Resource Manager)
/skill deploy-app           # アプリデプロイ (コンテナビルド→プッシュ→デプロイ)
/skill verify               # E2E テスト実行
```

## Skills & Workflow

### Skills (6つ)

| スキル | 説明 |
|--------|------|
| **hearing** | 対話的ヒアリングで要件を構造化JSON (`hearing/result.json`) に変換 |
| **generate-terraform** | ヒアリング結果からOCI Terraformコードを自動生成 |
| **generate-app** | デモアプリのソースコード + Dockerfile を生成 (多言語対応) |
| **deploy-infra** | OCI Resource Manager 経由で Terraform plan/apply を実行 (セルフヒーリング付き) |
| **deploy-app** | コンテナイメージをビルド → OCIR にプッシュ → 対象コンピュートにデプロイ |
| **verify** | ヘルスチェック・E2Eテストを実行し、デプロイ結果を検証 |

### Workflow

| ワークフロー | 説明 |
|-------------|------|
| **build-demo-env** | 上記6スキルを順番にチェイン実行するメインオーケストレーター |

### Pythonヘルパーモジュール (`artifacts/src/`)

| モジュール | 説明 |
|-----------|------|
| `oci_cli.py` | OCI CLI ラッパー (認証・コンパートメント解決) |
| `oci_rm.py` | OCI Resource Manager API (スタック作成・plan・apply・destroy) |
| `deployer.py` | Docker ビルド・OCIR プッシュ・各種コンピュートへのデプロイ |
| `e2e_runner.py` | HTTP ヘルスチェック・エンドポイントテスト |
| `reporter.py` | 結果フォーマッティング |

## 対応サービス

### コンピュート

- OKE (Oracle Kubernetes Engine)
- Container Instances
- Compute Instance
- Functions

### 言語・フレームワーク

- Python (FastAPI, Flask)
- Node.js (Express)
- Java, Go 等

### データベース

- Autonomous Database (ATP)
- MySQL Database Service

### その他OCIサービス

- Object Storage
- Streaming
- API Gateway
- Load Balancer
- Logging

## プロジェクト構成

```
Galley/
├── artifacts/
│   ├── skills/                  # 6つのスキル定義
│   │   ├── hearing.md
│   │   ├── generate-terraform.md
│   │   ├── generate-app.md
│   │   ├── deploy-infra.md
│   │   ├── deploy-app.md
│   │   ├── verify.md
│   │   ├── tf-templates/        # Terraform コンポーネントテンプレート
│   │   └── hearing-templates/   # ヒアリング質問テンプレート
│   ├── workflows/
│   │   └── build-demo-env.md    # メインワークフロー
│   ├── src/                     # Python ヘルパーモジュール
│   └── pyproject.toml
├── generated/                   # 生成されたデモプロジェクト
├── hearing/                     # ヒアリングセッション結果
├── tests/                       # テスト
├── CLAUDE.md                    # AI-DLC ワークフロールール
└── README.md
```

## 開発

```bash
# 依存関係のインストール
pip install -e ".[dev]"

# テスト実行
pytest

# 生成済みデモの確認
ls generated/
```

## mcpブランチとの違い

| 項目 | main (Skills/Workflows) | mcp (MCP Server) |
|------|------------------------|-------------------|
| 実行方式 | Claude Code Skills/Workflows | MCP Server (FastMCP) |
| デプロイ | ローカル実行 | OCI Container Instance + API Gateway |
| 接続 | Claude Code CLI 内で直接実行 | Claude Desktop 等から MCP 経由で接続 |
| Deploy to OCI ボタン | なし | あり |
| 依存関係 | 軽量 (requests のみ) | OCI SDK, FastMCP 等 |

## ライセンス

TBD
