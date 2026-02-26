# 設計: Terraform ワークフロー フィードバック修正

## P0: terraform init 自動実行

**変更箇所**: `src/galley/services/infra.py`

- `_ensure_terraform_init()` メソッドを追加
- `.terraform` ディレクトリが存在しない場合に `terraform init -no-color -input=false` を自動実行
- `run_terraform_plan`, `run_terraform_apply`, `run_terraform_destroy` から呼び出し

## P1: terraform_dir パス返却

**変更箇所**: `src/galley/services/design.py`, `src/galley/tools/export.py`

- `export_iac()` の返却値に `terraform_dir` キーを追加（ファイル書き出し先のフルパス）
- ツール記述に「返却される terraform_dir を run_terraform_plan にそのまま渡せます」を追記

## P1: export_iac 実リソース生成

**変更箇所**: `src/galley/services/design.py`

- `_TF_RESOURCE_TEMPLATES` に10種のサービスのHCLテンプレートを定義
- `_TF_DEFAULTS` にサービスごとのデフォルト値を定義
- `_render_component_tf()` でテンプレートベースのHCL生成
- `_TF_REQUIRED_VARS` でコンポーネント依存の追加Terraform変数を自動生成
- `_TF_REQUIRED_DATA_SOURCES` でdata sourceブロックを自動追加
- 変数の重複排除ロジック

## P2: complete_hearing → save_architecture の案内

**変更箇所**: `src/galley/tools/hearing.py`

- `complete_hearing` ツールの返却値に `"next_step"` フィールドを追加

## P2: Terraform変数注入

**変更箇所**: `src/galley/services/infra.py`, `src/galley/tools/infra.py`

- `run_terraform_plan`, `run_terraform_apply`, `run_terraform_destroy` に `variables: dict[str, str] | None` パラメータを追加
- `_build_terraform_args()` で `-var key=value` 形式に変換
