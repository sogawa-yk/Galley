# Business Logic Model - Unit 2: Terraform Generation

## Overview

Terraform Generation Skillは2段階のフローで動作する：
1. **ヒアリング結果解析**: result.jsonを読み込み、必要なOCIリソースを特定
2. **Terraformコード生成**: リソースタイプ別にTerraformファイルを生成

## フロー詳細

```
hearing/result.json
      |
      v
[Phase 1: リソース特定]
      | result.json解析
      | 必要なOCIリソースをリストアップ
      | リソース間の依存関係を解析
      v
[Phase 2: コード生成]
      | provider.tf (OCIプロバイダー設定)
      | variables.tf (変数定義)
      | network.tf (VCN, Subnet, etc.)
      | compute.tf (OKE/CI/Compute/Functions)
      | database.tf (ATP/MySQL, 必要な場合)
      | storage.tf (Object Storage, 必要な場合)
      | lb.tf (Load Balancer, 必要な場合)
      | outputs.tf (出力値定義)
      | terraform.tfvars (変数値)
      v
generated/{project-name}/terraform/
```

## Phase 1: リソース特定

### 入力
- `hearing/result.json`

### 処理
1. result.jsonの各フィールドからOCIリソースをマッピング:

| result.json field | OCI Resource | Terraform Resource |
|---|---|---|
| compute_type: oke | OKE Cluster + Node Pool | oci_containerengine_cluster |
| compute_type: container_instances | Container Instance | oci_container_instances_container_instance |
| compute_type: compute | Compute Instance | oci_core_instance |
| compute_type: functions | Functions Application + Function | oci_functions_application |
| database.type: atp | Autonomous Database | oci_database_autonomous_database |
| database.type: mysql | MySQL DB System | oci_mysql_mysql_db_system |
| network.vcn: new | VCN + Subnets + Security Lists | oci_core_vcn |
| network.load_balancer: true | Load Balancer | oci_load_balancer_load_balancer |
| additional_services: object_storage | Object Storage Bucket | oci_objectstorage_bucket |
| additional_services: streaming | Streaming Stream | oci_streaming_stream |
| additional_services: api_gateway | API Gateway | oci_apigateway_gateway |

2. リソース間の依存関係を解析（例: ComputeはVCN/Subnetに依存）

### 出力
- リソースリスト（タイプ、パラメータ、依存関係）

## Phase 2: コード生成

### 生成方針
- **OCI公式Terraformモジュール** (`terraform-oci-*`) が存在するリソースはモジュール参照で生成
- **モジュールが存在しないリソース** はClaude Codeが直接リソース定義を動的生成
- **State管理**: Resource Managerに完全委任（backend設定不要）
- **ファイル分割**: リソースタイプ別

### 公式モジュール対応表

| Resource | Module | 動的生成 |
|---|---|---|
| VCN + Network | terraform-oci-vcn | モジュール使用 |
| OKE | terraform-oci-oke | モジュール使用 |
| Compute | - | 動的生成 |
| Container Instances | - | 動的生成 |
| Functions | - | 動的生成 |
| ATP | - | 動的生成 |
| MySQL | - | 動的生成 |
| Load Balancer | - | 動的生成 |
| Object Storage | - | 動的生成 |

### 生成ファイル一覧

| File | Content | Always |
|---|---|---|
| `provider.tf` | OCI provider設定、required_providers | Yes |
| `variables.tf` | compartment_id, region等の変数定義 | Yes |
| `terraform.tfvars` | 変数のデフォルト値 | Yes |
| `network.tf` | VCN, Subnet, Security List, Internet/NAT Gateway | Yes (新規VCN時) |
| `compute.tf` | OKE/CI/Compute/Functionsリソース | Yes |
| `database.tf` | ATP/MySQL | No (DB要求時のみ) |
| `storage.tf` | Object Storage, etc. | No (追加サービス要求時のみ) |
| `lb.tf` | Load Balancer | No (LB要求時のみ) |
| `outputs.tf` | エンドポイントURL、リソースOCID等の出力 | Yes |
