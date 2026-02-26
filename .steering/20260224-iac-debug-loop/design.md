# 設計: IaCデバッグループ改善

## R1: update_terraform_file ツール

**変更箇所**: `src/galley/services/infra.py`, `src/galley/tools/infra.py`

- `InfraService.update_terraform_file(session_id, file_path, new_content)` を追加
- `storage.get_session_dir(session_id) / "terraform"` 配下のファイルのみ許可
- `file_path` は terraform ディレクトリからの相対パス（例: "components.tf"）
- パストラバーサル防止: `..` を含むパスを拒否、resolveしたパスがterraform_dir配下か検証
- セッション・アーキテクチャの存在確認を実施
- ツール層: `tools/infra.py` に `update_terraform_file` を登録

## R2: ネットワーク系テンプレート

**変更箇所**: `src/galley/services/design.py`, `config/oci-services.yaml`

6サービスのテンプレートを `_TF_RESOURCE_TEMPLATES` に追加:
- `subnet` → `oci_core_subnet`（vcn_id, cidr_block, display_name, prohibit_public_ip_on_vnic）
- `internet_gateway` → `oci_core_internet_gateway`（vcn_id）
- `route_table` → `oci_core_route_table`（vcn_id, route_rules）
- `security_list` → `oci_core_security_list`（vcn_id, ingress/egress rules）
- `nat_gateway` → `oci_core_nat_gateway`（vcn_id）
- `service_gateway` → `oci_core_service_gateway`（vcn_id, services data source）

`_TF_DEFAULTS` に各サービスのデフォルト値を追加。
`_TF_REQUIRED_VARS` に vcn_id 依存を追加。
`config/oci-services.yaml` にサービス定義を追加。

## R3: terraform.tfvars.example 生成

**変更箇所**: `src/galley/services/design.py`

`export_iac()` 内で `terraform.tfvars.example` を生成:
- 基本変数（region, compartment_id）のサンプル値
- コンポーネント依存の追加変数のサンプル値
- 各行にコメントで説明を付与

## R4: subnet_id変数矛盾解消

**変更箇所**: `src/galley/services/design.py`

`export_iac()` に以下のロジックを追加:
1. `_build_local_references(components)` — アーキテクチャ内のコンポーネントからローカル参照マップを構築
   - subnet → `var.subnet_id` を `oci_core_subnet.{name}.id` に置換
   - vcn → `var.vcn_id` を `oci_core_vcn.{name}.id` に置換
2. 変数生成時: ローカル参照で解決される変数を `_TF_REQUIRED_VARS` から除外
3. テンプレートレンダリング後: ローカル参照マップで `var.xxx` を置換

## R5: OCI CLI設定ガイド

**変更箇所**: `src/galley/services/infra.py`, `src/galley/tools/infra.py`

- `run_oci_cli` のエラーハンドリングを強化
- OCI CLI設定ファイル未検出時に具体的なセットアップ手順を stderr に追加
- `CLIResult` に `setup_hint` フィールドを追加し、設定ガイドを含める

## R6: Terraformエラー構造化

**変更箇所**: `src/galley/services/infra.py`, `src/galley/models/infra.py`

- `TerraformErrorDetail` Pydanticモデルを追加: `{file, line, message, suggestion}`
- `TerraformResult.errors` フィールド追加（`list[TerraformErrorDetail] | None`）
- `InfraService._parse_terraform_errors(stderr)` メソッドで正規表現ベースのパース
- Terraformのエラー形式: `Error: ... on file.tf line N:`
