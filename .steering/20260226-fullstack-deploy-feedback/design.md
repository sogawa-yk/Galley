# 設計

## C2: export_all修正

### 現状の問題
`export_all`がTerraformファイルを返す際、初期生成時のテンプレートを返しており、`update_terraform_file`での修正が反映されない。

### 修正方針
`export_all`（および`export_iac`）がTerraformファイルを返す際、セッションのterraform_dirから実際のファイル内容を読み込んで返すようにする。

### 調査対象
- `src/galley/tools/export.py` — export_all, export_iacの実装
- `src/galley/services/infra.py` — terraform_dir管理

## C3: Terraformテンプレート品質改善

### 現状の問題
IaC生成（`design.py`のexport_iac相当）が生成するTerraformコードに以下の品質問題:
1. Service GatewayでリージョンCIDR名がハードコード
2. サブネット参照の不整合
3. セキュリティリストのポート設定不備
4. OKEクラスタの必須属性欠落
5. ルートテーブルの設定不足

### 修正方針
`design.py`のIaC生成テンプレート/ロジックを修正し、以下を実現:
- `data.oci_core_services`からの動的サービスCIDR取得をデフォルト化
- サブネット参照の整合性チェック強化
- セキュリティルールのポート設定デフォルト値改善
- OKE固有の必須属性をテンプレートに追加
- ルートテーブルにService Gatewayルートを含める
