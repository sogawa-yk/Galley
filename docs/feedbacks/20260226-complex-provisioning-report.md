# Galley 複雑構成プロビジョニングテスト レポート

**実施日**: 2026-02-26
**テストツール**: mcp-gauge (トレーシング + 評価)
**対象**: Galley preview (FastMCP, ローカル実行)
**テストシナリオ**: IoTリアルタイムデータ分析プラットフォーム（19コンポーネント構成）

---

## テスト概要

### シナリオ

社内向けリアルタイムデータ分析プラットフォームを想定。IoTセンサーデータをStreamingで受信し、OCI Functionsで変換、OKE上のアプリケーションで可視化、API GatewayでREST APIを外部公開する構成。

### 構成コンポーネント（19個）

| カテゴリ | コンポーネント | 設定 |
|----------|---------------|------|
| ネットワーク | VCN (1) | 10.0.0.0/16 |
| | Public Subnet | 10.0.0.0/24 |
| | Private Subnet App | 10.0.1.0/24 |
| | Private Subnet DB | 10.0.2.0/24 |
| | Internet Gateway | - |
| | NAT Gateway | - |
| | Service Gateway | - |
| | Public Route Table | 0.0.0.0/0 → IGW |
| | Private Route Table | 0.0.0.0/0 → NAT GW |
| | Public Security List | TCP 443 from 0.0.0.0/0 |
| | Private Security List | TCP 8080 from 10.0.0.0/16 |
| コンピュート | OKE Cluster | E4.Flex, 3ノード, 1 OCPU/node |
| データベース | Autonomous DB (ATP) | 1 OCPU, 1TB, private endpoint |
| | NoSQL Database | 50 RU/50 WU/25GB |
| アプリケーション | API Gateway | public endpoint |
| | Load Balancer | flexible, public |
| | Streaming | 1 partition, 24h retention |
| | OCI Functions | 512MB, 60s timeout |
| ストレージ | Object Storage | Standard, versioning |

### 環境制約

- Always Free **使用不可**
- VCN: **1つまで**
- 同一シェイプのOCPU: **3つまで**

---

## テスト結果サマリー

| フェーズ | 結果 | 詳細 |
|----------|------|------|
| ヒアリング | OK | 10問回答、正常完了 |
| アーキテクチャ保存 | OK | 19コンポーネント、17接続 |
| バリデーション | **問題あり** | 0エラー/0警告（偽陰性） |
| IaC出力 | **問題あり** | 複数の生成バグ |
| Terraform Plan | OK | 20リソース作成予定 |
| Terraform Apply | **FAILED** | 8エラー（20中11成功、9失敗） |
| Terraform Destroy | OK | 11リソース正常削除 |

### mcp-gauge メトリクス

| メトリクス | 値 |
|-----------|-----|
| 総ツール呼び出し数 | 18（2セッション合計） |
| ユニークツール数 | 15 |
| エラー数（ツールレベル） | 0 |
| 総所要時間 | 約264秒（plan/apply/destroy含む） |
| gauge評価結果 | **FAILED**（`run_terraform_apply`がタイムアウトで未完了） |

---

## 発見された問題点

### Critical: IaC生成のバグ（Terraform Apply時に発覚）

#### C-1: サブネット割り当ての誤り

**症状**: API Gateway、Load Balancer、OKE endpoint、Functions Application が全て `private_subnet_db` に配置される。

**期待動作**: connections定義の `deployed_in` 関係に従い、適切なサブネットに配置されるべき。

**影響**:
- API Gateway: `endpointType must be valid` — public endpointをprivateサブネットに配置不可
- Load Balancer: `Private subnet ... is not allowed in a public loadbalancer`
- OKE: `must be a public subnet if public ip enabled` — publicエンドポイント有効なのにprivateサブネットを使用

**根本原因**: IaC生成ロジックがconnection定義の`deployed_in`関係を参照せず、最後のサブネット（private_subnet_db）をデフォルトで全リソースに使用している。

```hcl
# 生成されたコード（誤り）
resource "oci_apigateway_gateway" "api_gateway" {
  subnet_id = oci_core_subnet.private_subnet_db.id  # ← Public Subnetであるべき
}

resource "oci_load_balancer_load_balancer" "public_lb" {
  subnet_ids = [oci_core_subnet.private_subnet_db.id]  # ← Public Subnetであるべき
}
```

#### C-2: リソース名のサニタイズ不備

**症状**: display_nameがそのままOCIリソース名として使用され、OCI APIの命名規則に違反。

**影響**:
- NoSQL: `IoT Session Store` → スペース不可（`Table, index and unquoted field names may contain only alphanumeric values plus the character "_"`）
- Object Storage: `Data Lake` → スペース不可（`The name Data Lake may contain only letters, numbers, dashes and underscores`）

**改善案**: display_nameをTerraformリソース名に使う際に、スペースをアンダースコアに置換し、英数字+`_`+`-`のみに正規化する処理を追加。

#### C-3: Private Route TableがInternet Gatewayを参照

**症状**: private_route_tableのroute_rulesが`oci_core_internet_gateway.internet_gateway.id`を参照。

**期待動作**: プライベートルートテーブルは NAT Gateway を参照すべき。

```hcl
# 生成されたコード（誤り）
resource "oci_core_route_table" "private_route_table" {
  route_rules {
    network_entity_id = oci_core_internet_gateway.internet_gateway.id  # ← NAT GWであるべき
  }
}
```

#### C-4: Public SubnetにPrivate Route Tableが割り当て

**症状**: 全サブネット（public含む）が`private_route_table`を参照。

```hcl
resource "oci_core_subnet" "public_subnet" {
  route_table_id    = oci_core_route_table.private_route_table.id  # ← public_route_tableであるべき
  security_list_ids = [oci_core_security_list.private_security_list.id]  # ← public_security_listであるべき
}
```

#### C-5: API Gateway の endpoint_type が小文字

**症状**: `endpoint_type = "public"` → OCI APIは `"PUBLIC"` (大文字)を要求。

**エラー**: `endpointType must be valid`

### High: 構成上の欠落

#### H-1: OKE Node Poolリソースが未生成

**症状**: `oci_containerengine_cluster` のみ生成され、`oci_containerengine_node_pool` が生成されない。

**影響**: クラスタは作成されるがワーカーノードが0台のため、Podをスケジュールできない。node_count=3の設定が無視される。

#### H-2: ADBのプライベートエンドポイント設定が反映されない

**症状**: コンポーネント設定で `endpoint_type: "private"` を指定したが、Terraformに `subnet_id` や `nsg_ids` が設定されず、パブリックエンドポイントで作成される。

### Medium: バリデーションの偽陰性

#### M-1: validate_architectureが0エラー/0警告を返す

**症状**: 19コンポーネント/17接続の複雑な構成に対し、バリデーションが一切のエラーや警告を返さない。

**検出すべきだった問題**:
- ルートテーブルとサブネットの不整合（publicサブネットにprivateルートテーブル）
- パブリックリソース（LB, API GW）のプライベートサブネット配置
- OKEノードプール未定義
- リソース名の命名規則違反（スペース含み）
- Private Route TableがIGWを参照

### Medium: テナンシー制限・クォータ

#### M-2: Streaming パーティション上限超過

**エラー**: `You exceeded the number of allowed partitions for your tenancy`

**改善案**: `list_available_services` のサービス定義で、テナンシー制約をサービスの注意事項として記載。または `validate_architecture` でクォータチェックの仕組みを導入。

#### M-3: Functions Application 数上限超過

**エラー**: `The application-count limit for this tenant has been exceeded`

#### M-4: ADB機能がテナンシーで無効

**エラー**: `You are attempting to use a feature that's not currently enabled for this tenancy`

**改善案**: ADBが利用不可の場合の代替（MySQL Database Serviceなど）をサジェストする機能。

### Low: 運用性・UX

#### L-1: run_terraform_apply のタイムアウト

**症状**: gauge_proxy_callが300秒でタイムアウトするが、OKE+ADBを含むapplyは10分以上かかる。

**影響**: エージェントがapplyの結果を直接取得できず、`get_rm_job_status`で手動ポーリングが必要になる。

**改善案**: 非同期ジョブモデルの採用（apply開始→job_id返却→ポーリング）、またはより長いタイムアウト設定。

#### L-2: 環境変数の依存が不明確

**症状**: `GALLEY_REGION` と `GALLEY_WORK_COMPARTMENT_ID` が未設定だとRM操作が失敗するが、エラーメッセージからは原因が分かりにくい。

**改善案**: 起動時のヘルスチェックで必須環境変数の存在確認、またはRM操作時のバリデーションメッセージ改善。

---

## ツール説明文の品質（gauge_lint結果）

| 指標 | 値 |
|------|-----|
| 総ツール数 | 28 |
| 総問題数 | 64 |
| エラー（missing-param-description） | 42 |
| 警告（missing-return-description） | 22 |

**主な問題**: 全ツールの必須パラメータ（`session_id`, `terraform_dir`等）に `description` が欠落。FastMCPのdocstringからArgs部分は抽出されるが、JSON Schemaの `properties.*.description` フィールドには反映されていない。

---

## 改善提案（優先度順）

### P0: 即座に修正すべき

1. **サブネット割り当てロジックの修正**: connections定義の `deployed_in` 関係を参照し、各リソースを正しいサブネットに配置する
2. **リソース名サニタイズの追加**: display_nameからTerraformリソース名を生成する際にOCI命名規則に準拠した正規化を行う
3. **API Gateway endpoint_typeの大文字化**: `"public"` → `"PUBLIC"`, `"private"` → `"PRIVATE"`
4. **Private Route TableのNAT Gateway参照**: privateルートテーブルのデフォルトルートをNAT Gatewayに修正

### P1: 次スプリントで修正

5. **OKE Node Pool生成の追加**: クラスタ定義からnode_pool リソースを自動生成
6. **ADBプライベートエンドポイント対応**: endpoint_type設定に応じてsubnet_idとnsg_idsを設定
7. **validate_architectureの強化**: ネットワーク整合性、サブネット配置、命名規則のチェックを追加
8. **パラメータdescriptionの追加**: FastMCPの`Field(description=...)`でJSON Schema descriptionを設定

### P2: 中期的に改善

9. **クォータ事前チェック**: OCI Limitsサービスと連携し、validate_architectureでクォータ超過を事前検知
10. **非同期Applyワークフロー**: apply開始→ジョブID返却→ポーリングの3ステップに分離
11. **テナンシー機能チェック**: 利用可能なサービスをテナンシーの有効機能と照合

---

## 付録: Terraform Apply エラー一覧

| # | リソース | エラーコード | メッセージ |
|---|---------|------------|----------|
| 1 | oci_containerengine_cluster.app_cluster | 400-InvalidParameter | must be a public subnet if public ip enabled |
| 2 | oci_database_autonomous_database.transaction_db | 409-IncorrectState | feature not currently enabled for this tenancy |
| 3 | oci_nosql_table.iot_session_store | 400-InvalidParameter | Table names may contain only alphanumeric + "_" |
| 4 | oci_apigateway_gateway.api_gateway | 400-InvalidParameter | endpointType must be valid |
| 5 | oci_load_balancer_load_balancer.public_lb | 400-InvalidParameter | Private subnet not allowed in public loadbalancer |
| 6 | oci_streaming_stream.iot_event_stream | 400-LimitExceeded | partition limit exceeded |
| 7 | oci_functions_application.data_transform_app | 400-LimitExceeded | application-count limit exceeded |
| 8 | oci_objectstorage_bucket.data_lake | 400-InvalidBucketName | name may contain only letters, numbers, dashes, underscores |

### 成功したリソース（11/20）

VCN, Internet Gateway, NAT Gateway, Service Gateway, Public Subnet, Private Subnet App, Private Subnet DB, Public Route Table, Private Route Table, Public Security List, Private Security List

---
## 対応結果
- **対応日**: 2026-02-26
- **ステアリング**: `.steering/20260226-complex-provisioning-fix/`
- **対応内容の要約**: IaC生成ロジック(design.py)の8件のバグを修正。サブネット割り当てのpublic/private区別対応、OCI APIリソース名サニタイズ(nosql/objectstorage/streaming)、API Gateway endpoint_type大文字化、Private Route TableのNAT GW参照修正、Public SubnetへのPublic RT/SL割り当て、OKE Node Pool生成テンプレート追加、ADBプライベートエンドポイント対応。バリデーション強化として命名規則チェックとサブネット配置整合性チェックを追加。全258テストパス、ruff/mypy全クリア。
