# 開発ガイドライン (Development Guidelines)

## コーディング規約

### 命名規則

#### 変数・関数

```python
# 変数: snake_case、名詞または名詞句
session_data = load_session(session_id)
hearing_result = get_hearing_result(session_id)
available_services = list_available_services()

# 関数: snake_case、動詞で始める
def create_session() -> Session: ...
def validate_architecture(architecture: Architecture) -> list[ValidationResult]: ...
def export_mermaid(session_id: str) -> str: ...

# 定数: UPPER_SNAKE_CASE
DEFAULT_CACHE_TTL = 600  # 10分
MAX_RETRY_COUNT = 3
OBJECT_STORAGE_NAMESPACE = "galley"

# Boolean: is_, has_, should_, can_ で始める
is_completed = session.status == "completed"
has_architecture = session.architecture is not None
can_deploy = all_validations_passed
```

#### クラス・型

```python
# クラス: PascalCase、名詞
class HearingService: ...
class ArchitectureValidator: ...
class StorageService: ...

# Pydanticモデル: PascalCase
class Session(BaseModel): ...
class Component(BaseModel): ...

# 型エイリアス: PascalCase
SessionStatus = Literal["in_progress", "completed"]
ComponentConfig = dict[str, Any]

# Enum: PascalCase（クラス）、UPPER_SNAKE_CASE（値）
class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
```

### コードフォーマット

**インデント**: 4スペース（Python標準）

**行の長さ**: 最大120文字

**フォーマッター**: Ruff（Black互換モード）

**設定**:
```toml
# pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.format]
quote-style = "double"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```

### 型ヒント

すべての関数・メソッドに型ヒントを付ける:

```python
# 引数と戻り値に型ヒントを付ける
async def create_session(self) -> Session: ...

async def save_answer(
    self,
    session_id: str,
    question_id: str,
    value: str | list[str],
) -> Answer: ...

# Noneを返す可能性がある場合はOptionalではなく | None
async def load_session(self, session_id: str) -> Session | None: ...
```

**型チェック**: mypy（strictモード）

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
```

**テスト**: pytest + pytest-asyncio

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### コメント規約

**docstring（Google style）**:
```python
async def validate_architecture(self, session_id: str) -> list[ValidationResult]:
    """アーキテクチャ構成をバリデーションルールに基づいて検証する。

    Args:
        session_id: 検証対象のセッションID。

    Returns:
        検出された問題のリスト。問題がない場合は空リスト。

    Raises:
        SessionNotFoundError: 指定されたセッションが存在しない場合。
        ArchitectureNotFoundError: セッションにアーキテクチャが未設定の場合。
    """
```

**インラインコメント**:
```python
# なぜそうするかを説明する
# Resource Principalが利用できない場合はAPI Key認証にフォールバック
if not is_resource_principal_available():
    signer = get_api_key_signer()
```

### エラーハンドリング

**原則**:
- カスタム例外クラスを定義し、エラーの種類を明確にする
- MCPツールからの応答は構造化されたエラー情報を返す
- 予期しないエラーはログ出力して上位に伝播

**カスタム例外の定義**:
```python
class GalleyError(Exception):
    """Galleyの基底例外クラス。"""

class SessionNotFoundError(GalleyError):
    """セッションが見つからない場合の例外。"""
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Session not found: {session_id}")
        self.session_id = session_id

class ValidationError(GalleyError):
    """バリデーションエラー。"""
    def __init__(self, message: str, details: list[dict]) -> None:
        super().__init__(message)
        self.details = details

class TerraformError(GalleyError):
    """Terraform実行エラー。"""
    def __init__(self, message: str, stderr: str, exit_code: int) -> None:
        super().__init__(message)
        self.stderr = stderr
        self.exit_code = exit_code
```

**MCPツールでのエラーハンドリング**:
```python
@mcp.tool()
async def create_session() -> dict:
    try:
        session = await hearing_service.create_session()
        return {"session_id": session.id, "status": session.status}
    except GalleyError as e:
        return {"error": type(e).__name__, "message": str(e)}
```

## Git運用ルール

### ブランチ戦略

**ブランチ種別**:
- `main`: 本番環境にデプロイ可能な状態
- `feature/{機能名}`: 新機能開発
- `fix/{修正内容}`: バグ修正
- `refactor/{対象}`: リファクタリング
- `docs/{対象}`: ドキュメント更新

**フロー**:
```
main
  ├─ feature/hearing-tools
  ├─ feature/design-validation
  ├─ fix/session-persistence
  └─ docs/update-architecture
```

### コミットメッセージ規約

**フォーマット**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: コードフォーマット
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド、補助ツール等

**Scope**: `hearing`, `design`, `infra`, `app`, `storage`, `server`, `models`, `validators`, `deploy`, `config`

Scopeはリポジトリ構造のディレクトリ（services/、tools/、models/等）またはドメイン概念（hearing、design等）に対応させる。

**例**:
```
feat(hearing): ヒアリングセッションの作成・管理機能を実装

HearingServiceにcreate_session、save_answer、complete_hearingを実装。
セッションデータはObject Storageに永続化される。

- Session、Answer、HearingResultのPydanticモデルを追加
- StorageServiceにセッションCRUD操作を追加
- MCPツールとして登録

Closes #12
```

### プルリクエストプロセス

**作成前のチェック**:
- [ ] 全てのテストがパス（`pytest`）
- [ ] リントエラーがない（`ruff check`）
- [ ] 型チェックがパス（`mypy`）
- [ ] フォーマットが適用されている（`ruff format --check`）

**PRテンプレート**:
```markdown
## 概要
[変更内容の簡潔な説明]

## 変更理由
[なぜこの変更が必要か]

## 変更内容
- [変更点1]
- [変更点2]

## テスト
- [ ] ユニットテスト追加
- [ ] 統合テスト追加（該当する場合）
- [ ] 手動テスト実施

## 関連Issue
Closes #[Issue番号]
```

## テスト戦略

### テストの種類

#### ユニットテスト

**対象**: 個別のサービスクラス・関数

**カバレッジ目標**: 80%

**例**:
```python
import pytest
from galley.services.hearing import HearingService
from galley.models.session import Session

class TestHearingService:
    async def test_create_session_returns_new_session(
        self, hearing_service: HearingService
    ) -> None:
        session = await hearing_service.create_session()

        assert session.id is not None
        assert session.status == "in_progress"
        assert session.answers == {}

    async def test_save_answer_stores_answer(
        self, hearing_service: HearingService
    ) -> None:
        session = await hearing_service.create_session()
        answer = await hearing_service.save_answer(
            session.id, "purpose", "REST API構築"
        )

        assert answer.question_id == "purpose"
        assert answer.value == "REST API構築"

    async def test_complete_hearing_requires_answers(
        self, hearing_service: HearingService
    ) -> None:
        session = await hearing_service.create_session()

        with pytest.raises(ValidationError):
            await hearing_service.complete_hearing(session.id)
```

#### 統合テスト

**対象**: MCPプロトコル経由のツール呼び出し

**例**:
```python
import json
from fastmcp import Client

def parse_tool_result(result: object) -> dict:
    """CallToolResultからJSONデータを抽出する。"""
    content = result.content  # type: ignore[union-attr]
    assert len(content) > 0
    return json.loads(content[0].text)  # type: ignore[union-attr]

async def test_hearing_flow_via_mcp(mcp_server) -> None:
    async with Client(mcp_server) as client:  # type: ignore[arg-type]
        # セッション作成
        result = await client.call_tool("create_session", {})
        data = parse_tool_result(result)
        assert "session_id" in data

        session_id = data["session_id"]

        # 回答保存
        result = await client.call_tool("save_answer", {
            "session_id": session_id,
            "question_id": "purpose",
            "value": "REST API構築",
        })
        data = parse_tool_result(result)
        assert data["question_id"] == "purpose"
```

**注意**: FastMCP 2.x の `Client.call_tool()` は `CallToolResult` オブジェクトを返す。レスポンスデータには `result.content[0].text` でアクセスする。ツール名には `galley:` 等のプレフィックスは付かない。

#### E2Eテスト

**対象**: 実際のOCI環境での全体フロー

**例**:
```python
@pytest.mark.e2e
async def test_terraform_plan_apply_destroy(infra_service) -> None:
    session_id = "test-session"
    terraform_dir = "/tmp/test-terraform"

    # Plan
    plan_result = await infra_service.run_terraform_plan(session_id, terraform_dir)
    assert plan_result.success

    # Apply
    apply_result = await infra_service.run_terraform_apply(session_id, terraform_dir)
    assert apply_result.success

    # Destroy
    destroy_result = await infra_service.run_terraform_destroy(session_id, terraform_dir)
    assert destroy_result.success
```

### テスト命名規則

**パターン**: `test_{対象メソッド}_{条件}_{期待結果}`

```python
# 正常系
def test_create_session_returns_new_session(): ...
def test_save_answer_stores_answer_in_session(): ...
def test_validate_architecture_returns_empty_for_valid(): ...

# 異常系
def test_save_answer_raises_error_for_invalid_session(): ...
def test_complete_hearing_raises_error_without_answers(): ...
def test_run_terraform_plan_returns_error_for_invalid_tf(): ...
```

### モック・フィクスチャの使用

**原則**:
- OCI SDK クライアント、Object Storageアクセスはモック化
- 外部プロセス実行（Terraform、OCI CLI）はモック化
- ビジネスロジックは実装を使用

**例**:
```python
@pytest.fixture
def mock_storage() -> AsyncMock:
    storage = AsyncMock(spec=StorageService)
    storage.save_session = AsyncMock()
    storage.load_session = AsyncMock(return_value=None)
    return storage

@pytest.fixture
def hearing_service(mock_storage: AsyncMock) -> HearingService:
    return HearingService(storage=mock_storage, config=test_config)
```

## コードレビュー基準

### レビューポイント

**機能性**:
- [ ] PRDの要件を満たしているか
- [ ] エッジケースが考慮されているか
- [ ] エラーハンドリングが適切か

**可読性**:
- [ ] 命名が明確か
- [ ] 型ヒントが付いているか
- [ ] docstringが適切か

**保守性**:
- [ ] レイヤー間の依存関係ルールに従っているか
- [ ] 重複コードがないか
- [ ] 責務が明確に分離されているか

**セキュリティ**:
- [ ] 入力検証が適切か（特にOCI CLI実行、ファイルパス操作）
- [ ] 機密情報がハードコードされていないか
- [ ] IAMの最小権限原則に従っているか

## 開発環境セットアップ

### 必要なツール

| ツール | バージョン | インストール方法 |
|--------|-----------|-----------------|
| Python | 3.12+ | devcontainerに含まれる |
| uv | 最新安定版 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | 最新安定版 | devcontainerに含まれる |

### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd galley

# 2. devcontainerの起動
#    VS Code: コマンドパレット → "Dev Containers: Reopen in Container"
#    CLI: devcontainer up --workspace-folder .

# 3. 依存関係のインストール
uv sync

# 4. OCI CLI設定（ローカル開発時のみ、Resource Principalが使えない環境）
oci setup config
# ~/.oci/config にデフォルトプロファイルが作成される
# tenancy、user、region、鍵ファイルパスを設定

# 5. テストの実行
uv run pytest

# 6. リンター・フォーマッターの実行
uv run ruff check .
uv run ruff format .
uv run mypy src/

# 7. 開発サーバーの起動（ローカル）
uv run python -m galley.server
```

### よく使うコマンド

```bash
# テスト
uv run pytest                          # 全テスト実行
uv run pytest tests/unit/              # ユニットテストのみ
uv run pytest tests/integration/       # 統合テストのみ
uv run pytest -k "test_hearing"        # 特定テストのみ
uv run pytest --cov=galley             # カバレッジ付き

# コード品質
uv run ruff check .                    # リントチェック
uv run ruff check . --fix              # 自動修正
uv run ruff format .                   # フォーマット
uv run mypy src/                       # 型チェック

# サーバー起動
uv run python -m galley.server         # MCPサーバー起動
```
