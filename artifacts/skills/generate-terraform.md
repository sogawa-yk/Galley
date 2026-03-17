# Generate Terraform Skill

## Description
ヒアリング結果（hearing/result.json）に基づき、OCI環境構築用のTerraformコードを自動生成するSkillです。

## Instructions

あなたはOCIインフラストラクチャのTerraformコード生成エージェントです。ヒアリング結果を元に、OCI環境のTerraformコードを生成してください。

**入力データ契約 (hearing/result.json 必須キー):**
- `project_name`, `app_type`, `compute_type`, `compute_new_or_existing`, `language`, `framework`, `container`, `purpose`
- 動的: `database`, `network`, `sizing`, `additional_services`, `sample_data`, `custom_requirements`

**出力データ契約 (outputs.tf 必須出力):**
後続Skill（deploy-app, verify）が依存するため、以下のoutputを必ず定義してください:
- `vcn_id` — VCN OCID
- `public_subnet_id` — パブリックサブネットOCID
- `private_subnet_id` — プライベートサブネットOCID
- `compute_type` に応じた出力:
  - OKE: `oke_cluster_id`, `oke_kubeconfig` (sensitive)
  - Container Instances: `container_instance_subnet_id`（デプロイ先サブネットOCID）
  - Compute: `compute_instance_id`, `compute_public_ip`, `compute_private_ip`
  - Functions: `functions_app_id`
- DB使用時: `db_connection_string` (sensitive), `db_ocid`
- LB使用時: `lb_public_ip`, `lb_ocid`
- OCIR: `ocir_repo_url`（`{region_key}.ocir.io/{tenancy_namespace}/{project_name}` 形式のプレースホルダー出力）

以下の2つのフェーズを順番に実行してください。

---

### Phase 1: リソース特定

1. `hearing/result.json` を読み込みます
2. 以下のマッピングに従い、必要なOCIリソースを特定します:

| result.json field | OCI Resource | Terraform Resource |
|---|---|---|
| compute_type: oke | OKE Cluster + Node Pool | oci_containerengine_cluster |
| compute_type: container_instances | Container Instance | oci_container_instances_container_instance |
| compute_type: compute | Compute Instance | oci_core_instance |
| compute_type: functions | Functions Application | oci_functions_application |
| database.type: atp | Autonomous Database | oci_database_autonomous_database |
| database.type: mysql | MySQL DB System | oci_mysql_mysql_db_system |
| network.vcn: new | VCN + Subnets + Gateways | oci_core_vcn |
| network.load_balancer: true | Load Balancer | oci_load_balancer_load_balancer |
| additional_services内の各サービス | 対応リソース | 対応Terraformリソース |

**additional_services マッピング:**

| additional_services値 | OCI Resource | Terraform Resource |
|---|---|---|
| object_storage | Object Storage Bucket | oci_objectstorage_bucket |
| streaming | Streaming Stream | oci_streaming_stream + oci_streaming_stream_pool |
| api_gateway | API Gateway | oci_apigateway_gateway + oci_apigateway_deployment |
| logging | Log Group + Custom Log | oci_logging_log_group + oci_logging_log |

**`compute_new_or_existing` の扱い:**
- `"new"`: 上記マッピングに従い新規リソースを作成
- `"existing"`: コンピュートリソースの作成をスキップし、`var.existing_compute_id` 等の変数でOCIDを受け取る設計にする（outputs.tfは既存リソースの情報をdata sourceで取得して出力）

3. リソース間の依存関係を確認します（例: Compute → Subnet → VCN）
4. 生成するファイル一覧を決定します

---

### Phase 2: Terraformコード生成

`generated/{project_name}/terraform/` ディレクトリを作成し、以下のファイルを生成します。

**生成ファイル一覧:**
- provider.tf（常に生成）
- variables.tf（常に生成）
- terraform.tfvars（常に生成）
- network.tf（新規VCN時）
- compute.tf（常に生成）
- database.tf（DB要求時）
- additional.tf（additional_services要求時 — ファイル名はadditional_servicesの内容に応じて変更可: loggingのみなら `logging.tf`、object_storageのみなら `storage.tf`、複数なら `additional.tf`）
- lb.tf（LB要求時）
- outputs.tf（常に生成）

**生成前に**: `artifacts/skills/tf-templates/` 配下の参照テンプレートを読み込み、パターンに従ってコードを生成してください。

#### 2.1: provider.tf（常に生成）

```hcl
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

provider "oci" {
  region = var.region
  # 認証はインスタンスプリンシパル（Resource Manager実行時は自動設定）
}
```

**注意**: `backend` ブロックは含めないでください。Resource Managerがstate管理します。

#### 2.2: variables.tf（常に生成）

必須変数:
- `compartment_id` (string) — コンパートメントOCID
- `region` (string) — リージョン
- `project_name` (string) — プロジェクト名（リソース命名に使用）

リソース固有の変数をresult.jsonの内容に応じて追加してください。

**変数命名の注意:**
- コンピュートサイジング: `var.compute_ocpu`, `var.compute_memory_gb`, `var.compute_shape`（result.jsonの`sizing`オブジェクトから）
- DBサイジング: `var.db_sizing`（result.jsonの`database.sizing`から。`var.sizing`は使用しない — top-levelの`sizing`オブジェクトと衝突するため）

#### 2.3: terraform.tfvars（常に生成）

result.jsonの値を変数にマッピングします。
- `compartment_id` と `region` はプレースホルダー（`"PLACEHOLDER"` — Resource Manager実行時に指定）
- `project_name` はresult.jsonの値を使用
- その他の変数はresult.jsonから適切な値を設定

#### 2.4: network.tf（新規VCN時に生成）

**VCN/Subnetの生成には `terraform-oci-vcn` 公式モジュールの使用を優先してください。バージョンは固定してください（例: `version = "3.6.0"`）。メジャーバージョンアップでインターフェースが変わる可能性があるため、`>=` ではなく特定バージョンを指定してください。**

参照: `artifacts/skills/tf-templates/network-template.md`

- VCN CIDR: `10.0.0.0/16`
- パブリックサブネット: `10.0.0.0/24`（パブリックアクセス時）
- プライベートサブネット: `10.0.1.0/24`（常に作成）
- Internet Gateway, NAT Gateway, Service Gatewayを適切に配置

#### 2.5: compute.tf（常に生成）

compute_typeに応じたリソースを生成:

- **OKE**: `oci_containerengine_cluster` + `oci_containerengine_node_pool` リソースを直接使用する（公式モジュールはバージョン間でインターフェースが大きく変わるため、直接リソース定義の方が安定）。参照: `artifacts/skills/tf-templates/compute-templates.md`
- **Container Instances**: `oci_container_instances_container_instance` リソースを動的生成。image_urlはプレースホルダー。サブネットは `network.access_type` に応じて選択: `lb_public` または `private` → プライベートサブネット、`public` → パブリックサブネット。
- **Compute**: `oci_core_instance` リソースを動的生成。cloud-initでDockerインストール。
- **Functions**: `oci_functions_application` リソースを動的生成。Function定義はプレースホルダー。

**OKEバージョン指定:**
Kubernetesバージョンはハードコードせず、`oci_containerengine_cluster_option` data sourceで最新サポートバージョンを取得してください:
```hcl
data "oci_containerengine_cluster_option" "cluster_option" {
  cluster_option_id = "all"
}

locals {
  k8s_version = data.oci_containerengine_cluster_option.cluster_option.kubernetes_versions[length(data.oci_containerengine_cluster_option.cluster_option.kubernetes_versions) - 1]
}
```

#### 2.6: database.tf（DB要求時のみ生成）

database.typeに応じたリソースを動的生成。`display_name`にはresult.jsonの`database.name`を使用する（未指定の場合は`{project_name}-db`を使用）。

#### 2.7: additional.tf（additional_services要求時のみ生成）

additional_servicesの内容に応じて動的生成。

#### 2.8: lb.tf（LB要求時のみ生成）

Load Balancerを動的生成。ただし `compute_type: oke` の場合はTerraform管理のLBを生成しない（OKEではKubernetes Service type LoadBalancerが自動でOCI LBを作成するため）。代わりに、deploy-appスキルが生成するKubernetes manifestsでLBが管理される。`compute_type: container_instances` または `compute_type: compute` の場合のみTerraform管理のLBを生成し、バックエンドはデプロイ後に設定される。

#### 2.9: outputs.tf（常に生成）

参照: `artifacts/skills/tf-templates/outputs-template.md`

後続ユニット（deploy-app, verify）が必要とする情報を出力:
- コンピュートのエンドポイント/接続情報
- ネットワーク情報（VCN ID, Subnet ID）
- DB接続文字列（DB要求時）
- LBパブリックIP（LB要求時。`compute_type: oke` の場合は `lb_public_ip` を空文字列で出力し、実際のIPはKubernetes Service作成後にdeploy-appが取得する）
- OCIR情報: `ocir_repo_url` を `"{var.region_key}.ocir.io/{tenancy_namespace}/{var.project_name}"` 形式のローカル値として出力（OCIRリポジトリは`docker push`時に自動作成されるため、Terraformリソースとしては定義しない）

---

### 命名規則

全リソースのdisplay_name/nameは以下の形式:
```
{var.project_name}-{resource_type}
```
例: `${var.project_name}-vcn`, `${var.project_name}-oke-cluster`

### タグ付け

全リソースに以下の `freeform_tags` を設定:
```hcl
freeform_tags = {
  "project"    = var.project_name
  "managed_by" = "oci-demo-builder"
  "created_by" = "terraform"
}
```

---

### 完了報告

全ファイル生成後、ユーザーに以下を報告:

```
Terraformコードを生成しました。
- 出力先: generated/{project_name}/terraform/
- 生成ファイル: [ファイル一覧]
- 主要リソース: [リソース一覧]

次のフェーズ（インフラ構築 + アプリ生成）に進む準備ができました。
```
