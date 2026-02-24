# 要求内容

## 概要

E2E Terraformライフサイクルテストを追加し、`export_iac`で生成されるTerraformコードが実際に動作するかを自動検証できるようにする。

## 背景

Galleyは現在、全てのTerraform/OCI CLIコマンドをモックしてテストしている。そのため、`export_iac`で生成されるTerraformコードが実際に動作するかを自動検証できず、Claude Codeによる自律的な開発が困難。変更後に`uv run pytest tests/e2e/`で正しさを自律的に検証できる仕組みが必要。

## 実装対象の機能

### 1. `export_iac`の`variables.tf`動的生成修正

- 現在の`variables.tf`は`region`と`compartment_id`のみ宣言
- 6つのサービスタイプが未宣言の変数を参照しており、`terraform validate`が失敗する
- コンポーネントのサービスタイプに応じて`variables.tf`に変数宣言を動的追加
- data sourceブロック（compute用）を`main.tf`に動的追加
- 同一変数の重複排除

### 2. E2Eテストの追加

- `test_terraform_validate.py`: 全10サービスタイプのterraform validate（OCI不要）
- `test_terraform_plan.py`: VCN/ADBのterraform plan（OCI API接続、リソース作成なし）
- `test_terraform_lifecycle.py`: VCNのplan→apply→re-plan（冪等性）→destroy（実リソース作成）

### 3. テスト構成の整理

- E2Eテストをデフォルトのpytest実行から除外（`--ignore=tests/e2e`）
- `e2e`と`e2e_lifecycle`マーカーの追加

## 受け入れ条件

### variables.tf動的生成
- [x] computeコンポーネント使用時に`image_id`, `subnet_id`変数が宣言される
- [x] compute使用時に`oci_identity_availability_domains` data sourceがmain.tfに追加される
- [x] 複数コンポーネントが同じ変数を要求する場合、重複しない
- [x] VCNのみの場合は追加変数が生成されない
- [x] 既存ユニットテスト195件が全て通過する

### E2Eテスト
- [x] 全10サービスタイプで`terraform validate`が成功する
- [x] VCN/ADBで`terraform plan`が成功する（OCI API接続）
- [x] VCNのフルライフサイクル（plan→apply→re-plan→destroy）が動作する
- [x] `uv run pytest`（デフォルト）でE2Eテストが除外される
- [x] `uv run pytest tests/e2e/`でE2Eテストが実行できる

## 成功指標

- `uv run pytest` で既存195テストが全て通過
- `uv run pytest tests/e2e/test_terraform_validate.py` で12テストが全て通過
- `uv run pytest tests/e2e/test_terraform_plan.py` で3テストが全て通過

## スコープ外

以下はこのフェーズでは実装しません:

- CI/CDパイプラインへのE2Eテスト統合
- OCI quota管理の自動化
- テスト用コンパートメントの自動作成

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/environment.md` - 環境情報（OCI情報）
