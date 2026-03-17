# Business Rules - Unit 2: Terraform Generation

## BR-1: モジュール選択ルール

### BR-1.1: 公式モジュール優先
- OCI公式Terraformモジュール（`terraform-oci-*`）が存在するリソースは、モジュール参照でコードを生成する
- モジュールが存在しない場合のみ、`resource` ブロックを直接生成する（動的生成）

### BR-1.2: モジュールバージョン
- モジュールのsource指定にはバージョン制約を含める
- 例: `source = "oracle-terraform-modules/vcn/oci"` + `version = ">= 3.0.0"`

## BR-2: ファイル生成ルール

### BR-2.1: provider.tf（常に生成）
- `required_providers` に hashicorp/oci を指定
- provider "oci" ブロックにregionのみ設定（認証はインスタンスプリンシパルのためauth設定不要）
- Resource Manager実行前提のため `terraform { backend }` ブロックは含めない

### BR-2.2: variables.tf（常に生成）
- `compartment_id` (string, 必須)
- `region` (string, 必須)
- `project_name` (string, 必須) — リソース命名に使用
- リソース固有の変数（shape, sizing等）

### BR-2.3: terraform.tfvars（常に生成）
- result.jsonの値を変数に変換
- compartment_idはプレースホルダー（RM実行時に指定）
- regionはプレースホルダー（RM実行時に指定）

### BR-2.4: outputs.tf（常に生成）
- 後続ユニット（deploy-app, verify）が必要とする情報を出力
- 必須出力: コンピュートのエンドポイント情報、ネットワーク情報
- DB出力: 接続文字列（DB要求時のみ）
- LB出力: パブリックIP（LB要求時のみ）

## BR-3: リソース命名ルール

### BR-3.1: 命名規則
- 全リソースのdisplay_name/nameに `project_name` を接頭辞として使用
- フォーマット: `{project_name}-{resource_type}`
- 例: `ecommerce-demo-vcn`, `ecommerce-demo-oke-cluster`

### BR-3.2: タグ付け
- 全リソースに `freeform_tags` を設定:
  - `project`: project_name
  - `managed_by`: "oci-demo-builder"
  - `created_by`: "terraform"

## BR-4: ネットワーク生成ルール

### BR-4.1: 新規VCN（network.vcn: new）
- VCN CIDR: `10.0.0.0/16`（デフォルト）
- パブリックサブネット: `10.0.0.0/24`（access_typeがpublic or lb_publicの場合）
- プライベートサブネット: `10.0.1.0/24`（常に作成）
- Internet Gateway: パブリックアクセス時に作成
- NAT Gateway: プライベートサブネット用に作成
- Service Gateway: OCI内部サービスアクセス用に作成

### BR-4.2: 既存VCN（network.vcn: existing）
- data sourceで既存VCN/Subnetを参照
- vcn_idはvariablesで受け取る

## BR-5: コンピュート生成ルール

### BR-5.1: OKE
- クラスターとノードプール1つを作成
- ノードプールのsizingはresult.jsonのsizingフィールドに従う
- Kubernetes API: パブリックエンドポイント
- ノード: プライベートサブネット

### BR-5.2: Container Instances
- Container Instanceを作成
- shape: result.jsonのsizingに従う
- image_url: プレースホルダー（deploy-appが後から設定）

### BR-5.3: Compute Instance
- Compute Instanceを作成
- cloud-initスクリプトでDockerインストール

### BR-5.4: Functions
- Functions Applicationを作成
- Function定義はプレースホルダー（deploy-appが後から設定）

## BR-6: 出力ディレクトリルール

### BR-6.1: 出力先
- `generated/{project_name}/terraform/` に全ファイルを出力
- project_nameはresult.jsonから取得

### BR-6.2: 既存ファイルの扱い
- 出力先ディレクトリが既に存在する場合は上書き
- 前回の生成物をクリーンアップしてから新規生成
