# 設計書

## アーキテクチャ概要

レイヤードアーキテクチャに従い、MCPプロトコル層→サービス層→データアクセス層の3層構造を採用する。MVP段階ではOCI Object Storageの代わりにローカルファイルシステムを使用するため、StorageServiceにはローカルファイルシステム実装を用意する。

```
MCPプロトコル層 (tools/, resources/, prompts/)
    ↓
サービス層 (services/)
    ↓
データアクセス層 (storage/)
    ↓
ローカルファイルシステム (.galley/)
```

## コンポーネント設計

### 1. MCPサーバー (server.py)

**責務**:
- FastMCPインスタンスの作成と設定
- ツール・リソース・プロンプトの登録
- サーバー起動

**実装の要点**:
- `FastMCP("galley")` でサーバーインスタンスを作成
- 各ツールモジュールからツール登録関数を呼び出し
- `__main__.py` でエントリポイントを提供

### 2. 設定管理 (config.py)

**責務**:
- 環境変数・設定値の一元管理
- ヒアリング質問定義の読み込み

**実装の要点**:
- Pydantic `BaseSettings` でサーバー設定を管理
- データディレクトリのパス管理（デフォルト: `.galley/`）

### 3. データモデル (models/)

**責務**:
- Pydanticモデルによる型安全なデータ定義

**ファイル構成**:
- `session.py`: Session、SessionStatus、Answer、HearingResult、Requirement
- `errors.py`: GalleyError、SessionNotFoundError、ValidationError

**実装の要点**:
- `model_config = ConfigDict(strict=True)` は不要（過剰制約を避ける）
- datetimeフィールドはUTC前提

### 4. ストレージサービス (storage/service.py)

**責務**:
- セッションデータのCRUD操作
- ローカルファイルシステムへの永続化

**実装の要点**:
- MVP段階ではローカルファイルシステムに保存（`.galley/sessions/{session_id}/session.json`）
- 将来のOCI Object Storage移行を見据えた抽象インターフェース
- JSON形式でデータを保存

### 5. ヒアリングサービス (services/hearing.py)

**責務**:
- セッションライフサイクル管理
- 回答保存とバリデーション
- ヒアリング完了と結果構造化

**実装の要点**:
- StorageServiceに依存
- ヒアリング質問定義（config/hearing-questions.yaml）に基づくバリデーション
- complete_hearingは回答から構造化されたHearingResultを生成

### 6. MCPツール (tools/hearing.py)

**責務**:
- FastMCPツールの定義と登録
- サービス層への委譲

**実装の要点**:
- `@mcp.tool()` デコレータでツールを登録
- エラーハンドリング: GalleyError → 構造化エラーレスポンス
- ツール名は `create_session`, `save_answer` 等（FastMCPがプレフィックスを付与）

### 7. MCPリソース (resources/hearing.py)

**責務**:
- ヒアリング質問定義のMCPリソース公開

**実装の要点**:
- `@mcp.resource()` で質問定義をリソースとして公開

### 8. MCPプロンプト (prompts/hearing.py)

**責務**:
- ヒアリング開始・再開用のプロンプト定義

**実装の要点**:
- `@mcp.prompt()` でヒアリングフローのプロンプトを公開

## データフロー

### ヒアリングフロー
```
1. create_session → HearingService.create_session → StorageService.save_session → session.json保存
2. save_answer → HearingService.save_answer → StorageService.save_session → session.json更新
3. complete_hearing → HearingService.complete_hearing → 回答→HearingResult変換 → StorageService.save_session
4. get_hearing_result → HearingService.get_hearing_result → StorageService.load_session → HearingResult返却
```

## エラーハンドリング戦略

### カスタムエラークラス

```python
class GalleyError(Exception): ...
class SessionNotFoundError(GalleyError): ...
class HearingNotCompletedError(GalleyError): ...
class HearingAlreadyCompletedError(GalleyError): ...
```

### エラーハンドリングパターン

MCPツール層で例外をキャッチし、構造化エラーレスポンスを返す:
```python
{"error": "session_not_found", "message": "Session {id} not found"}
```

## テスト戦略

### ユニットテスト
- `tests/unit/models/test_session.py`: データモデルのバリデーション
- `tests/unit/services/test_hearing.py`: HearingServiceのビジネスロジック
- `tests/unit/storage/test_service.py`: StorageServiceのCRUD操作

### 統合テスト
- `tests/integration/test_hearing_flow.py`: ヒアリングフロー全体のMCPプロトコル経由テスト

## 依存ライブラリ

```toml
[project]
dependencies = [
    "fastmcp>=2.0",
    "pydantic>=2.0,<3",
    "pyyaml>=6.0",
    "uvicorn",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio",
    "ruff",
    "mypy",
    "types-PyYAML",
]
```

## ディレクトリ構造

```
galley/
├── src/
│   └── galley/
│       ├── __init__.py
│       ├── __main__.py          # エントリポイント
│       ├── server.py            # MCPサーバー
│       ├── config.py            # 設定管理
│       ├── models/
│       │   ├── __init__.py
│       │   ├── session.py       # Session, Answer, HearingResult
│       │   └── errors.py        # カスタム例外
│       ├── services/
│       │   ├── __init__.py
│       │   └── hearing.py       # HearingService
│       ├── storage/
│       │   ├── __init__.py
│       │   └── service.py       # StorageService
│       ├── tools/
│       │   ├── __init__.py
│       │   └── hearing.py       # ヒアリングMCPツール
│       ├── resources/
│       │   ├── __init__.py
│       │   └── hearing.py       # ヒアリングMCPリソース
│       └── prompts/
│           ├── __init__.py
│           └── hearing.py       # ヒアリングMCPプロンプト
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # 共通フィクスチャ
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── test_session.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── test_hearing.py
│   │   └── storage/
│   │       ├── __init__.py
│   │       └── test_service.py
│   └── integration/
│       ├── __init__.py
│       └── test_hearing_flow.py
├── config/
│   ├── hearing-flow.yaml
│   └── hearing-questions.yaml
├── pyproject.toml
└── .python-version
```

## 実装の順序

1. pyproject.toml と .python-version の作成
2. データモデル (models/)
3. カスタム例外 (models/errors.py)
4. 設定管理 (config.py)
5. ストレージサービス (storage/)
6. ヒアリングサービス (services/)
7. 設定ファイル (config/)
8. MCPツール (tools/)
9. MCPリソース (resources/)
10. MCPプロンプト (prompts/)
11. サーバーエントリポイント (server.py, __main__.py)
12. ユニットテスト
13. 統合テスト
14. 品質チェック

## セキュリティ考慮事項

- セッションIDはUUID v4で生成（推測困難）
- ファイルパスのディレクトリトラバーサル防止（session_idの検証）

## パフォーマンス考慮事項

- MVP段階ではローカルファイルシステムを使用するため、パフォーマンス要件は緩い
- 将来のObject Storage移行を見据え、async/awaitで設計

## 将来の拡張性

- StorageServiceをプロトコルベースで設計し、Object Storage実装への切り替えを容易にする
- サービス層は永続化の詳細を知らない設計
