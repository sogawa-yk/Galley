# タスクリスト: Terraform ワークフロー フィードバック修正

## 実装タスク

- [x] P0: `_ensure_terraform_init()` メソッドを `InfraService` に追加
- [x] P0: `run_terraform_plan`, `apply`, `destroy` から `_ensure_terraform_init()` を呼び出し
- [x] P1: `export_iac()` の返却値に `terraform_dir` パスを追加
- [x] P1: `export_iac` ツール説明に `terraform_dir` の使い方を記載
- [x] P1: `_TF_RESOURCE_TEMPLATES` に10種のHCLテンプレートを定義
- [x] P1: `_TF_DEFAULTS` にデフォルト値を定義
- [x] P1: `_render_component_tf()` でテンプレートベースのHCL生成
- [x] P1: `_TF_REQUIRED_VARS` でコンポーネント依存の変数自動生成
- [x] P1: `_TF_REQUIRED_DATA_SOURCES` でdata sourceブロックの自動追加
- [x] P2: `complete_hearing` レスポンスに `next_step` フィールド追加
- [x] P2: `run_terraform_plan/apply/destroy` に `variables` パラメータ追加
- [x] P2: `_build_terraform_args()` で `-var` フラグ変換

## テスト

- [x] `test_export_iac_generates_real_resource_definitions` - スケルトンでないことを確認
- [x] `test_export_iac_compute_adds_dynamic_variables` - compute用追加変数
- [x] `test_export_iac_compute_adds_data_source` - compute用data source
- [x] `test_export_iac_deduplicates_variables` - 変数重複排除
- [x] `test_export_iac_vcn_no_extra_variables` - VCNのみで追加変数なし
- [x] `test_export_iac_objectstorage_adds_namespace_variable` - objectstorage用変数
- [x] 既存テスト回帰なし（195 passed）

## 追加修正（実装検証で発見）

- [x] `_ensure_terraform_init()` の `calling_command` パラメータ型を `str` → `TerraformCommand` に修正
- [x] `TerraformCommand` 型エイリアスを `models/infra.py` で定義し、`services/infra.py` で使用
- [x] `test_design.py` の余分な空行を削除（ruff format違反）
- [x] `tests/e2e/conftest.py` の未使用 `asyncio` import を削除
- [x] `tests/e2e/test_terraform_lifecycle.py` の行長超過を修正
- [x] `middleware.py` の型注釈を追加（`ASGIApp`, `RequestResponseEndpoint`）
- [x] `tools/hearing.py` の `yaml.safe_load` 戻り値に型注釈を追加

## 実装後の振り返り

- **実装完了日**: 2026-02-24
- **計画と実績の差分**:
  - フィードバック5件の機能修正は既にコード上に実装済み（一部unstaged）であったため、新規コーディングは不要だった
  - 実装検証（implementation-validator）で型安全性の問題が発見され、追加修正7件を実施
  - 特に `_ensure_terraform_init` の `calling_command` パラメータが `str` 型だったのを `TerraformCommand` Literal型に修正し、mypy互換性を改善
  - 既存の `middleware.py` と `tools/hearing.py` にもmypy指摘があり、合わせて修正
- **学んだこと**:
  - Literal型エイリアスを定義して再利用すると、型安全性とコードの一貫性が向上する
  - ruff format + mypy の組み合わせで既存コードの品質問題も検出できる
- **次回への改善提案**:
  - CIパイプラインに `mypy src/` を追加し、型エラーの早期検出を強化する
  - e2eテストファイルも ruff format の対象に含めて自動フォーマットする
