# 設計書

## アーキテクチャ概要

既存のレイヤードアーキテクチャに従い、設計層のコンポーネントを追加する。

```
MCPプロトコル層:
  tools/design.py       — 設計系MCPツール（add_component, remove_component等）
  tools/export.py       — エクスポート系MCPツール（export_summary等）
  resources/design.py   — 設計関連MCPリソース（OCIサービス一覧等）
  prompts/design.py     — 設計支援MCPプロンプト

サービス層:
  services/design.py    — DesignService（設計のビジネスロジック）

バリデーション層（クロスカッティング）:
  validators/architecture.py — ArchitectureValidator（ルールベースの検証）

データモデル:
  models/architecture.py — Architecture, Component, Connection
  models/validation.py   — ValidationResult, ValidationRule
  models/session.py      — Session（architectureフィールド追加）

設定ファイル:
  config/oci-services.yaml                       — OCIサービス定義
  config/validation-rules/connection-requirements.yaml — 接続要件ルール
```

## コンポーネント設計

### 1. データモデル（models/architecture.py）

**責務**:
- Architecture, Component, Connection のPydanticモデル定義
- JSONシリアライゼーション対応

**実装の要点**:
- 機能設計書のデータモデル定義に厳密に従う
- Component.id はUUID v4で自動生成
- Architecture.validation_results は Optional（バリデーション実行前はNone）

### 2. バリデーションモデル（models/validation.py）

**責務**:
- ValidationResult, ValidationRule のPydanticモデル定義

**実装の要点**:
- ValidationRuleはYAMLファイルからの読み込みに対応する構造
- severity は "error" | "warning" | "info" のLiteral型

### 3. Session モデル更新（models/session.py）

**責務**:
- architectureフィールドの追加

**実装の要点**:
- `architecture: Architecture | None = None` を追加
- 既存のテストに影響を与えない（Noneデフォルト）

### 4. DesignService（services/design.py）

**責務**:
- アーキテクチャの保存・更新
- コンポーネントの追加・削除・設定変更
- バリデーション実行の委譲
- エクスポート機能
- OCIサービス一覧の提供

**実装の要点**:
- HearingServiceと同じパターン（storage + config_dir依存）
- セッションのワークフロー状態を検証（ヒアリング完了後のみ設計可能）
- ArchitectureValidatorへのバリデーション委譲
- コンポーネント削除時に関連Connectionも削除

### 5. ArchitectureValidator（validators/architecture.py）

**責務**:
- YAMLバリデーションルールの読み込み
- アーキテクチャに対するルール適用
- ValidationResultの生成

**実装の要点**:
- config/validation-rules/ からYAMLを読み込み
- ルールの条件マッチング（source_service, target_service）
- 要件チェック（target_config等）
- ルールのキャッシュ（インスタンス内メモリ）

### 6. MCPツール（tools/design.py, tools/export.py）

**責務**:
- FastMCP @mcp.tool() デコレータでツール登録
- DesignServiceへの委譲
- エラーハンドリング（GalleyError → dict形式）

**実装の要点**:
- hearing_tools.py と同じパターンで実装
- 入出力は機能設計書のスキーマに従う

### 7. MCPリソース（resources/design.py）

**責務**:
- OCIサービス一覧リソースの公開

### 8. MCPプロンプト（prompts/design.py）

**責務**:
- 自動設計モード用プロンプト
- 対話型設計モード用プロンプト

## データフロー

### 自動設計フロー
```
1. LLMが get_hearing_result でヒアリング結果を取得
2. LLMがヒアリング結果を分析し、アーキテクチャを生成
3. save_architecture でアーキテクチャを保存
4. validate_architecture でバリデーション実行
```

### 対話型設計フロー
```
1. list_available_services でOCIサービス一覧を取得
2. add_component でコンポーネントを追加
3. configure_component で設定変更
4. validate_architecture でバリデーション実行
5. 問題があれば修正を繰り返す
6. export_all でエクスポート
```

## エラーハンドリング戦略

### カスタムエラークラス

```python
class ArchitectureNotFoundError(GalleyError):
    """セッションにアーキテクチャが未設定の場合。"""

class ComponentNotFoundError(GalleyError):
    """指定されたコンポーネントが見つからない場合。"""

class ArchitectureValidationError(GalleyError):
    """バリデーションルールの読み込みエラー等。"""
```

### エラーハンドリングパターン

既存パターンに従い、MCPツール層で `GalleyError` をキャッチして `{"error": ..., "message": ...}` 形式で返却。

## テスト戦略

### ユニットテスト
- `tests/unit/models/test_architecture.py`: Architecture, Component, Connectionモデルのテスト
- `tests/unit/validators/test_architecture.py`: ArchitectureValidatorのルール適用テスト
- `tests/unit/services/test_design.py`: DesignServiceの各メソッドテスト

### 統合テスト
- `tests/integration/test_design_flow.py`: MCPプロトコル経由の設計フロー一連テスト

## 依存ライブラリ

新しい依存は不要。既存のpydantic, pyyaml, fastmcpで実装可能。

## ディレクトリ構造

```
追加/変更されるファイル:
  src/galley/models/architecture.py     (新規)
  src/galley/models/validation.py       (新規)
  src/galley/models/session.py          (変更: architectureフィールド追加)
  src/galley/models/errors.py           (変更: 新エラークラス追加)
  src/galley/validators/__init__.py     (新規)
  src/galley/validators/architecture.py (新規)
  src/galley/services/design.py         (新規)
  src/galley/tools/design.py            (新規)
  src/galley/tools/export.py            (新規)
  src/galley/resources/design.py        (新規)
  src/galley/prompts/design.py          (新規)
  src/galley/server.py                  (変更: 設計層の登録追加)
  config/oci-services.yaml              (新規)
  config/validation-rules/              (新規ディレクトリ)
  config/validation-rules/connection-requirements.yaml (新規)
  tests/unit/models/test_architecture.py      (新規)
  tests/unit/validators/__init__.py           (新規)
  tests/unit/validators/test_architecture.py  (新規)
  tests/unit/services/test_design.py          (新規)
  tests/integration/test_design_flow.py       (新規)
  tests/conftest.py                           (変更: 設計系フィクスチャ追加)
```

## 実装の順序

1. データモデル（models/architecture.py, models/validation.py, session.py更新）
2. エラークラス追加（models/errors.py）
3. 設定ファイル（config/oci-services.yaml, validation-rules/）
4. ArchitectureValidator（validators/architecture.py）
5. DesignService（services/design.py）
6. MCPツール・リソース・プロンプト（tools/design.py, tools/export.py, resources/design.py, prompts/design.py）
7. server.py更新
8. ユニットテスト
9. 統合テスト
10. 品質チェック

## セキュリティ考慮事項

- コンポーネントIDはUUID v4で自動生成（推測不可能）
- session_idのバリデーションは既存StorageServiceのディレクトリトラバーサル防止に依存
- export_iacで生成するTerraformコードにはハードコードされた秘密情報を含めない

## パフォーマンス考慮事項

- バリデーションルールはインスタンス変数としてキャッシュ（初回読み込みのみ）
- OCIサービス定義もキャッシュ
- エクスポート処理は文字列操作のみで軽量

## 将来の拡張性

- ArchitectureValidatorのルール追加はYAMLファイル追加のみで可能
- oci-services.yamlへのサービス追加でlist_available_servicesが自動的に拡張
- StorageServiceをOCI Object Storage実装に切り替えてもDesignServiceは変更不要
