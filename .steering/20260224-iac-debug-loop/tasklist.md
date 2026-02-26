# タスクリスト: IaCデバッグループ改善

## R1: update_terraform_file ツール

- [x] `InfraService.update_terraform_file()` メソッドをサービス層に追加
- [x] `tools/infra.py` に `update_terraform_file` MCPツールを登録
- [x] `test_infra.py` にユニットテスト追加（正常系・パストラバーサル・存在しないファイル）

## R2: ネットワーク系テンプレート

- [x] `_TF_RESOURCE_TEMPLATES` に6サービス（subnet, internet_gateway, route_table, security_list, nat_gateway, service_gateway）のテンプレートを追加
- [x] `_TF_DEFAULTS` と `_TF_REQUIRED_VARS` にデフォルト値・変数定義を追加
- [x] `config/oci-services.yaml` にサービス定義を追加
- [x] `test_design.py` にテスト追加

## R3: terraform.tfvars.example 生成

- [x] `export_iac()` に `terraform.tfvars.example` 生成ロジックを追加
- [x] `test_design.py` にテスト追加

## R4: subnet_id変数矛盾解消

- [x] `DesignService._build_local_references()` メソッドを追加
- [x] `export_iac()` の変数生成・テンプレートレンダリングにローカル参照解決を適用
- [x] `test_design.py` にテスト追加

## R5: OCI CLI設定ガイド

- [x] `CLIResult` に `setup_hint` フィールドを追加
- [x] `InfraService.run_oci_cli()` でOCI設定ファイル未検出エラーにヒントを付与
- [x] `tools/infra.py` の `run_oci_cli` ツール説明を更新

## R6: Terraformエラー構造化

- [x] `models/infra.py` に `TerraformErrorDetail` モデルを追加し `TerraformResult.errors` フィールドを追加
- [x] `InfraService._parse_terraform_errors()` メソッドを追加
- [x] `run_terraform_plan` 等で失敗時にエラーパースを実行
- [x] `test_infra.py` にテスト追加

## テスト

- [x] 既存テスト回帰なし（215 passed）

## 実装後の振り返り

- **実装完了日**: 2026-02-24
- **計画と実績の差分**:
  - R6のTerraformエラーパース正規表現で、lazy quantifier (`+?`) が optional groupと組み合わさるとメッセージが1文字しかマッチしない問題が発生。greedy (`+`) に修正して解決。
  - ruff formatで4ファイルの再フォーマットが必要だった（テンプレート文字列のインデント差異）。
- **学んだこと**:
  - 正規表現でoptional group (`(?:...)?`) とlazy quantifier (`+?`) を組み合わせると最小マッチが優先されるため、greedy quantifierを使うべき。
  - `_build_local_references()` のようなvar参照解決パターンは、今後 `route_table` の `var.gateway_id` 等に拡張可能。
- **次回への改善提案**:
  - `update_terraform_file` にセッションロック取得を追加し、Terraform実行中の競合を防止する（検証レポートで推奨）。
  - `nat_gateway`, `route_table`, `service_gateway` のテンプレート生成テストを追加する（現在3サービスが未テスト）。
