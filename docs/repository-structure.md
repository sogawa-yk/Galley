# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造

```
galley/
├── src/
│   └── galley/                # Pythonパッケージルート
│       ├── __init__.py
│       ├── server.py          # MCPサーバーエントリポイント
│       ├── config.py          # 設定管理
│       ├── models/            # データモデル定義（__init__.py含む）
│       ├── services/          # サービス層（__init__.py含む）
│       ├── storage/           # データアクセス層（__init__.py含む）
│       ├── tools/             # MCPツール定義（__init__.py含む）
│       ├── resources/         # MCPリソース定義（__init__.py含む）
│       ├── prompts/           # MCPプロンプト定義（__init__.py含む）
│       └── validators/        # バリデーションロジック（__init__.py含む）
├── tests/                     # テストコード
│   ├── unit/                  # ユニットテスト
│   ├── integration/           # 統合テスト
│   └── e2e/                   # E2Eテスト
├── config/                    # 設定・定義ファイル
│   ├── hearing-flow.yaml      # ヒアリングフロー定義
│   ├── hearing-questions.yaml # ヒアリング質問定義
│   ├── oci-services.yaml      # OCI利用可能サービス定義
│   └── validation-rules/      # バリデーションルール
│       ├── connection-requirements.yaml
│       ├── region-availability.yaml
│       ├── shape-constraints.yaml
│       └── network-best-practices.yaml
├── deploy/                    # 配布用Terraformファイル
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── api-gateway.tf
│   ├── container-instance.tf
│   ├── object-storage.tf
│   ├── network.tf
│   └── iam.tf
├── docker/                    # コンテナ関連
│   └── Dockerfile
├── docs/                      # プロジェクトドキュメント
│   ├── ideas/                 # 下書き・アイデア
│   ├── product-requirements.md
│   ├── functional-design.md
│   ├── architecture.md
│   ├── repository-structure.md
│   ├── development-guidelines.md
│   └── glossary.md
├── .steering/                 # 作業単位のドキュメント
├── .claude/                   # Claude Code設定
│   ├── skills/                # スキル定義
│   └── agents/                # サブエージェント定義
├── pyproject.toml             # プロジェクト設定・依存関係
├── uv.lock                    # 依存関係ロックファイル
├── CLAUDE.md                  # Claude Code設定ファイル
├── .gitignore
└── .python-version            # Pythonバージョン指定
```

## ディレクトリ詳細

### src/galley/ (ソースコードディレクトリ)

#### server.py

**役割**: FastMCPベースのMCPサーバーのエントリポイント。ツール・リソース・プロンプトの登録とサーバー起動。

#### config.py

**役割**: 環境変数・設定値の管理。Object Storageバケット名、リージョン等のサーバー設定を一元管理。

#### models/

**役割**: Pydanticモデルによるデータモデル定義

**配置ファイル**:
- `session.py`: Session、Answer、HearingResult
- `architecture.py`: Architecture、Component、Connection
- `validation.py`: ValidationResult、ValidationRule
- `template.py`: TemplateMetadata、TemplateParameter
- `infra.py`: TerraformResult、RMStack、RMJob、CLIResult
- `deploy.py`: DeployResult、AppStatus

**命名規則**:
- ファイル名: snake_case、ドメイン概念に対応
- クラス名: PascalCase

**依存関係**:
- 依存可能: Pydantic、標準ライブラリ
- 依存禁止: services/、storage/、tools/

#### services/

**役割**: ビジネスロジックの実装。各機能ドメインに対応するサービスクラスを配置。

**配置ファイル**:
- `hearing.py`: HearingService — ヒアリングセッション管理
- `design.py`: DesignService — アーキテクチャ設計管理
- `infra.py`: InfraService — Terraform実行・OCI操作
- `app.py`: AppService — テンプレート管理・アプリデプロイ

**命名規則**:
- ファイル名: snake_case、機能ドメインに対応
- クラス名: `{Domain}Service`（例: `HearingService`）

**依存関係**:
- 依存可能: models/、storage/、validators/
- 依存禁止: tools/、resources/、prompts/

#### storage/

**役割**: OCI Object Storageへのデータアクセス層。OCIクライアントの管理。

**配置ファイル**:
- `service.py`: StorageService — Object Storage CRUD操作
- `oci_client.py`: OCIClientFactory — Resource Principal認証とOCIクライアント生成

**命名規則**:
- ファイル名: snake_case

**依存関係**:
- 依存可能: models/、OCI SDK、標準ライブラリ
- 依存禁止: services/、tools/

#### tools/

**役割**: MCPツールの定義。FastMCPの `@mcp.tool()` デコレータでツールを登録。

**配置ファイル**:
- `hearing.py`: ヒアリング層ツール（create_session、save_answer等）
- `design.py`: 設計層ツール（add_component、validate_architecture等）
- `infra.py`: インフラ層ツール（run_terraform_plan、run_oci_cli等）
- `app.py`: アプリケーション層ツール（list_templates、build_and_deploy等）
- `export.py`: エクスポートツール（export_summary、export_mermaid等）

**命名規則**:
- ファイル名: snake_case、機能ドメインに対応
- ツール関数名: snake_case、MCPツール名と一致

**依存関係**:
- 依存可能: services/、models/
- 依存禁止: storage/（サービス層を経由してアクセス）

#### resources/

**役割**: MCPリソースの定義。FastMCPの `@mcp.resource()` デコレータでリソースを登録。

**配置ファイル**:
- `hearing.py`: ヒアリング関連リソース（質問定義等）
- `design.py`: 設計関連リソース（サービス一覧等）

**依存関係**:
- 依存可能: services/、models/
- 依存禁止: storage/

#### prompts/

**役割**: MCPプロンプトの定義。FastMCPの `@mcp.prompt()` デコレータでプロンプトを登録。

**配置ファイル**:
- `hearing.py`: ヒアリング開始・再開用プロンプト
- `design.py`: 設計支援用プロンプト
- `deploy.py`: デプロイ支援用プロンプト

**依存関係**:
- 依存可能: models/
- 依存禁止: services/、storage/

#### validators/

**役割**: アーキテクチャバリデーションのロジック。サービス層とデータアクセス層の両方に依存可能なクロスカッティングコンポーネント。services/ から呼び出され、storage/ からバリデーションルールを読み込む。

**配置ファイル**:
- `architecture.py`: ArchitectureValidator — バリデーションルールの読み込みと適用

**依存関係**:
- 依存可能: models/、storage/
- 依存禁止: services/（循環依存防止）、tools/

### tests/ (テストディレクトリ)

#### unit/

**役割**: ユニットテストの配置

**構造**:
```
tests/unit/
├── services/
│   ├── test_hearing.py
│   ├── test_design.py
│   ├── test_infra.py
│   └── test_app.py
├── validators/
│   └── test_architecture.py
├── models/
│   ├── test_session.py
│   └── test_architecture.py
└── storage/
    └── test_service.py
```

**命名規則**:
- パターン: `test_{テスト対象ファイル名}.py`
- テスト関数: `test_{対象メソッド}_{条件}_{期待結果}`

**ミラー構造の原則**: `tests/unit/` のサブディレクトリ構造は `src/galley/` のレイヤー構造をミラーする。例: `src/galley/services/hearing.py` のテストは `tests/unit/services/test_hearing.py` に配置。

#### integration/

**役割**: 統合テストの配置

**構造**:
```
tests/integration/
├── test_mcp_server.py         # MCPプロトコル経由のツール呼び出し
├── test_hearing_flow.py       # ヒアリング一連フロー
└── test_design_flow.py        # 設計一連フロー
```

#### e2e/

**役割**: E2Eテストの配置

**構造**:
```
tests/e2e/
├── test_full_workflow.py      # ヒアリング〜設計〜デプロイの全体フロー
└── test_terraform_cycle.py    # Terraform plan/apply/destroyサイクル
```

### config/ (設定ファイルディレクトリ)

**役割**: ヒアリング質問定義、バリデーションルール、OCIサービス定義などのYAML設定ファイル。リポジトリ内のマスターデータとして管理し、本番環境ではObject Storageに同期される。

**配置ファイル**:
- `hearing-flow.yaml`: ヒアリングの質問フロー定義
- `hearing-questions.yaml`: ヒアリング質問の詳細定義
- `oci-services.yaml`: 利用可能なOCIサービスの定義（名称、説明、設定項目）
- `validation-rules/`: バリデーションルールのYAMLファイル群

**config/ と Object Storage の関係**:
- `config/` はリポジトリ内のマスターデータ。開発者がGitで管理・レビューする
- 本番環境では、コンテナイメージのビルド時に `config/` の内容がObject Storageにアップロードされる
- 実行時にはObject Storageから読み込み、メモリにキャッシュする（バリデーションルール TTL: 10分）

### deploy/ (配布用Terraformディレクトリ)

**役割**: 利用者がGalley環境を構築するためのTerraformファイル

**配置ファイル**:
- `main.tf`: プロバイダー設定、変数参照
- `variables.tf`: 入力変数定義（compartment_id、region等）
- `outputs.tf`: 出力定義（MCPエンドポイントURL等）
- `api-gateway.tf`: API GatewayとDeployment
- `container-instance.tf`: Container Instance
- `object-storage.tf`: Object Storageバケット
- `network.tf`: VCN / Subnet / Security List
- `iam.tf`: Dynamic Group / IAM Policy

### docker/ (コンテナ関連ディレクトリ)

**役割**: GalleyコンテナイメージのDockerfile

## ファイル配置規則

### ソースファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| データモデル | src/galley/models/ | snake_case.py | session.py |
| サービスクラス | src/galley/services/ | snake_case.py | hearing.py |
| ストレージ | src/galley/storage/ | snake_case.py | service.py |
| MCPツール | src/galley/tools/ | snake_case.py | hearing.py |
| MCPリソース | src/galley/resources/ | snake_case.py | hearing.py |
| MCPプロンプト | src/galley/prompts/ | snake_case.py | hearing.py |
| バリデーター | src/galley/validators/ | snake_case.py | architecture.py |

### テストファイル

| テスト種別 | 配置先 | 命名規則 | 例 |
|-----------|--------|---------|-----|
| ユニットテスト | tests/unit/{layer}/ | test_{対象}.py | test_hearing.py |
| 統合テスト | tests/integration/ | test_{機能}.py | test_mcp_server.py |
| E2Eテスト | tests/e2e/ | test_{シナリオ}.py | test_full_workflow.py |

### 設定ファイル

| ファイル種別 | 配置先 | 命名規則 |
|------------|--------|---------|
| ヒアリング定義 | config/ | kebab-case.yaml |
| バリデーションルール | config/validation-rules/ | kebab-case.yaml |
| サービス定義 | config/ | kebab-case.yaml |
| プロジェクト設定 | プロジェクトルート | pyproject.toml |
| Dockerfile | docker/ | Dockerfile |

## 命名規則

### ディレクトリ名

- **レイヤーディレクトリ**: 複数形、snake_case
  - 例: `models/`, `services/`, `tools/`, `validators/`
- **設定ディレクトリ**: kebab-case
  - 例: `validation-rules/`

### ファイル名

- **Pythonモジュール**: snake_case
  - 例: `hearing.py`, `oci_client.py`, `architecture.py`
- **設定ファイル**: kebab-case
  - 例: `hearing-flow.yaml`, `oci-services.yaml`
- **Terraformファイル**: kebab-case
  - 例: `api-gateway.tf`, `container-instance.tf`

### Python命名規則

- **クラス名**: PascalCase（例: `HearingService`, `ArchitectureValidator`）
- **関数・メソッド名**: snake_case（例: `create_session`, `validate_architecture`）
- **変数名**: snake_case（例: `session_id`, `terraform_dir`）
- **定数名**: UPPER_SNAKE_CASE（例: `DEFAULT_CACHE_TTL`, `MAX_RETRY_COUNT`）
- **型エイリアス**: PascalCase（例: `SessionStatus`, `ComponentConfig`）

### テストファイル名

- パターン: `test_{テスト対象}.py`
- テスト関数: `test_{対象メソッド}_{条件}_{期待結果}`
- 例: `test_hearing.py` 内の `test_create_session_returns_new_session`

## 依存関係のルール

### レイヤー間の依存

```
MCPプロトコル層 (tools/, resources/, prompts/)
    ↓ (OK)
サービス層 (services/)
    ↓ (OK)
データアクセス層 (storage/)
    ↓ (OK)
外部システム (OCI API, Object Storage)
```

**禁止される依存**:
- storage/ → services/（逆方向依存）
- storage/ → tools/（逆方向依存）
- services/ → tools/（逆方向依存）
- tools/ → storage/（レイヤースキップ）

**例外**:
- models/ は全レイヤーから参照可能（データ転送オブジェクト）
- validators/ は services/ と storage/ の両方に依存可能

### モジュール間の依存

**循環依存の禁止**: サービス間の循環依存は、共通のモデルやインターフェースで解決する。

## スケーリング戦略

### 機能の追加

新しいMCPツールを追加する際の配置方針:

1. **既存ドメインの拡張**: 既存の `tools/{domain}.py` と `services/{domain}.py` にメソッドを追加
2. **新規ドメインの追加**: 新しい `tools/{new_domain}.py`、`services/{new_domain}.py`、`models/{new_domain}.py` を作成
3. **バリデーションルールの追加**: `config/validation-rules/` にYAMLファイルを追加

### ファイルサイズの管理

**ファイル分割の目安**:
- 1ファイル: 300行以下を推奨
- 300-500行: リファクタリングを検討
- 500行以上: 分割を強く推奨

## 特殊ディレクトリ

### .steering/ (ステアリングファイル)

**役割**: 特定の開発作業における「今回何をするか」を定義

**構造**:
```
.steering/
└── YYYYMMDD-task-name/
    ├── requirements.md
    ├── design.md
    └── tasklist.md
```

**命名規則**: `20260217-add-hearing-tools` 形式

### .claude/ (Claude Code設定)

**役割**: Claude Codeの設定とスキル定義

**構造**:
```
.claude/
├── skills/                    # スキル定義
│   ├── prd-writing/
│   ├── functional-design/
│   ├── architecture-design/
│   ├── repository-structure/
│   ├── development-guidelines/
│   ├── glossary-creation/
│   ├── steering/
│   ├── setup-project/
│   ├── review-docs/
│   └── add-feature/
└── agents/                    # サブエージェント定義
```

## 除外設定

### .gitignore

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# 仮想環境
.venv/

# IDE
.idea/
.vscode/

# 環境変数
.env
.env.local

# OS
.DS_Store

# テスト
.coverage
htmlcov/
.pytest_cache/

# ステアリングファイル
.steering/

# mypy
.mypy_cache/

# Ruff
.ruff_cache/
```
