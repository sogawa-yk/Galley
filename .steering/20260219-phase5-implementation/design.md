# 設計書

## アーキテクチャ概要

既存のレイヤードアーキテクチャに従い、アプリケーション層を追加する。

```
MCPプロトコル層 (tools/app.py, prompts/app.py)
    ↓
サービス層 (services/app.py)
    ↓
データアクセス層 (storage/service.py)
    ↓
ファイルシステム (.galley/sessions/{id}/app/)
```

## コンポーネント設計

### 1. models/app.py — データモデル

**責務**:
- TemplateMetadata, TemplateParameter: テンプレートメタデータの定義
- DeployResult: デプロイ結果
- AppStatus: アプリケーション状態

**実装の要点**:
- 機能設計書のデータモデル定義に準拠
- Pydanticモデルとして実装
- 既存のmodels/infra.pyと同じパターン

### 2. services/app.py — AppService

**責務**:
- テンプレート一覧取得（config/templates/からメタデータ読み込み）
- テンプレートからのプロジェクトスキャフォールディング
- アプリコードの更新（protected_paths保護付き）
- ビルド・デプロイ（現フェーズはスタブ）
- アプリ状態確認（現フェーズはスタブ）
- スナップショット保存・復元

**実装の要点**:
- `config_dir / "templates"` からテンプレートメタデータを読み込む
- `storage.data_dir / "sessions" / session_id / "app"` にプロジェクトファイルを配置
- スナップショットは `storage.data_dir / "sessions" / session_id / "snapshots"` に保存
- `protected_paths` は `fnmatch` パターンで保護対象を定義
- InfraServiceと同じく `StorageService` と `config_dir` を受け取る

### 3. tools/app.py — MCPツール登録

**責務**:
- `list_templates`: テンプレート一覧取得
- `scaffold_from_template`: テンプレートからプロジェクト生成
- `update_app_code`: アプリコード更新
- `build_and_deploy`: ビルド・デプロイ
- `check_app_status`: デプロイ状態確認

**実装の要点**:
- tools/infra.pyと同じエラーハンドリングパターン
- `register_app_tools(mcp, app_service)` 関数で登録

### 4. prompts/app.py — MCPプロンプト登録

**責務**:
- テンプレート選択ガイド
- アプリカスタマイズガイド
- デプロイフローガイド

### 5. models/errors.py — エラークラス追加

- `TemplateNotFoundError`: テンプレートが見つからない
- `ProtectedFileError`: 保護ファイルの変更拒否
- `AppNotScaffoldedError`: アプリが未生成の場合

## データフロー

### テンプレートからのプロジェクト生成
```
1. LLM → list_templates → AppService → config/templates/*/template.json 読み込み → 一覧返却
2. LLM → scaffold_from_template(session_id, template_name, params)
   → AppService → テンプレートファイルをコピー → パラメータ置換 → .galley/sessions/{id}/app/ に配置
3. LLM → update_app_code(session_id, file_path, new_content)
   → AppService → protected_paths チェック → スナップショット保存 → ファイル更新
```

### ビルド・デプロイ（スタブ）
```
1. LLM → build_and_deploy(session_id)
   → AppService → スタブ応答（OCI DevOps/OKE連携は未実装）
2. LLM → check_app_status(session_id)
   → AppService → ファイルシステム上の状態から返却
```

## エラーハンドリング戦略

### カスタムエラークラス

```python
class TemplateNotFoundError(GalleyError):
    def __init__(self, template_name: str) -> None: ...

class ProtectedFileError(GalleyError):
    def __init__(self, file_path: str) -> None: ...

class AppNotScaffoldedError(GalleyError):
    def __init__(self, session_id: str) -> None: ...
```

### エラーハンドリングパターン

既存の tools/infra.py と同じ:
```python
try:
    result = await app_service.method(...)
    return result.model_dump()  # or dict
except (GalleyError, ValueError) as e:
    return {"error": type(e).__name__, "message": str(e)}
```

## テスト戦略

### ユニットテスト (tests/unit/services/test_app.py)
- list_templates: テンプレート一覧取得（テンプレートあり/なし）
- scaffold_from_template: プロジェクト生成（正常/テンプレート不在/パラメータ不足）
- update_app_code: コード更新（正常/protected_path/未生成）
- build_and_deploy: スタブ応答
- check_app_status: 状態取得

### ユニットテスト (tests/unit/models/test_app.py)
- モデルのバリデーション

### 統合テスト (tests/integration/test_app_flow.py)
- MCPプロトコル経由のテンプレート生成→コード更新フロー

## 依存ライブラリ

新規追加なし（既存のPydantic, PyYAMLで対応可能）

## ディレクトリ構造

```
src/galley/
├── models/app.py           # 新規: TemplateMetadata, DeployResult, AppStatus
├── services/app.py         # 新規: AppService
├── tools/app.py            # 新規: register_app_tools
├── prompts/app.py          # 新規: register_app_prompts
├── models/errors.py        # 変更: エラークラス追加
├── server.py               # 変更: AppService登録追加

config/
└── templates/              # 新規: サンプルテンプレート
    └── rest-api-adb/
        ├── template.json   # テンプレートメタデータ
        └── app/            # テンプレートファイル
            └── ...

tests/
├── unit/
│   ├── models/test_app.py  # 新規
│   └── services/test_app.py # 新規
├── integration/
│   └── test_app_flow.py    # 新規
└── conftest.py             # 変更: app_service fixture追加
```

## セキュリティ考慮事項

- `update_app_code` の file_path にパストラバーサル防止（`..` や `~` を拒否）
- `protected_paths` による保護ファイルの変更拒否
- テンプレート名のサニタイズ

## パフォーマンス考慮事項

- テンプレートメタデータのキャッシュ（TTL: 5分、現フェーズではシンプルに都度読み込み）
- スナップショットはshutil.copytreeで高速コピー
