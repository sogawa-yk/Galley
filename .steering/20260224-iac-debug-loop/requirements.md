# 要件: IaCデバッグループ改善

## 参照元
`docs/feedbacks/20260224.md`

## 要件一覧

### R1 [Critical] Terraformファイル編集ツール
- `export_iac` で生成されたTerraformファイルを編集する手段を提供する
- `update_terraform_file(session_id, file_path, new_content)` ツールを追加
- セッションのterraformディレクトリ内のファイルのみ編集可能とする（パストラバーサル防止）

### R2 [High] ネットワーク系Terraformテンプレート
- subnet, internet_gateway, route_table, security_list, nat_gateway, service_gateway の6サービスのテンプレートを追加
- `save_architecture` で保存したconfigの値をHCLに直接展開する
- `oci-services.yaml` にサービス定義を追加

### R3 [High] terraform.tfvars.example 生成
- `export_iac` 時に `terraform.tfvars.example` を生成し、必要な変数のサンプル値を提供する

### R4 [Medium] subnet_id変数矛盾の解消
- アーキテクチャにsubnetコンポーネントが含まれる場合、`subnet_id` 変数を外部入力として要求しない
- テンプレート内の `var.subnet_id` をローカルリソース参照 (`oci_core_subnet.xxx.id`) に自動置換する
- 同様に `var.vcn_id` も VCN コンポーネントが存在する場合に自動置換する

### R5 [Medium] OCI CLI設定ガイド
- OCI CLI未設定時のエラーメッセージを改善し、設定方法を案内する
- ツール説明にInstance Principal / API Key認証の情報を追記

### R6 [Low] Terraformエラーの構造化レスポンス
- `TerraformResult` に `errors` フィールドを追加
- stderr を解析して `{file, line, message, suggestion}` 形式の構造化エラーリストを生成
- plan失敗時にLLMが自動修正しやすい形式で返す
