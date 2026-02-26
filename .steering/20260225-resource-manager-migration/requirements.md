# 要求内容

## 概要

Terraform実行をコンテナ内ローカル実行からOCI Resource Manager (RM) 経由に変更する。

## 背景

現在、GalleyはContainer Instance内で`terraform plan/apply/destroy`コマンドを直接実行している。この方式には以下の課題がある:

- コンテナにTerraformバイナリを同梱する必要がある（イメージサイズ増大）
- tfstateがコンテナのローカルファイルシステムに保存され、コンテナ再起動で消失する
- コンテナのリソース（CPU/メモリ）をTerraform実行が消費する
- ResourcePrincipal認証をproviderに手動設定する必要がある

OCI Resource Managerを使うことで:
- Terraformバイナリが不要になる
- tfstateはRM側でマネージドに管理される
- Terraform実行はOCIインフラ側で行われ、コンテナリソースを消費しない
- 認証はRM側で自動的に処理される（providerにauthパラメータ不要）

## RMの自動入力変数の活用

Resource Managerは以下の変数を自動的に入力する。これらをTerraformテンプレートで活用し、ユーザーが手動入力する変数を最小限にする:

| 変数名 | 自動入力される値 | 活用方法 |
|---|---|---|
| `tenancy_ocid` | スタックが存在するテナンシーのOCID | テナンシーレベルのリソース参照 |
| `compartment_ocid` | スタックが存在するコンパートメントのOCID | リソースの配置先 |
| `region` | スタックのリージョン | providerの設定 |
| `current_user_ocid` | ジョブを実行したユーザーのOCID | 監査・タグ付け |

**現在のテンプレートからの変更点**:
- `variable "region"` → `variable "region"` は維持（RM自動入力）
- `variable "compartment_id"` → `variable "compartment_ocid"` に改名（RM自動入力）
- `provider "oci" { region = var.region }` のみ（auth不要）

## 実装対象の機能

### 1. IaCテンプレート生成の変更（design.py）

- 生成する変数名を`compartment_id` → `compartment_ocid`に変更（RM自動入力対応）
- providerブロックから`auth = "ResourcePrincipal"`を削除（RM側で認証を自動処理）
- `tenancy_ocid`変数を追加（RM自動入力）

### 2. RM経由のTerraform実行（infra.py）

- `run_terraform_plan` → RMスタック作成/更新 + Planジョブ実行 + ポーリング
- `run_terraform_apply` → Applyジョブ実行 + ポーリング
- `run_terraform_destroy` → Destroyジョブ実行 + ポーリング
- OCI Python SDKの`ResourceManagerClient`を使用
- `ResourceManagerClientCompositeOperations`でジョブ完了待機

### 3. RMスタック管理

- セッションごとにRMスタックを作成・管理
- Terraformファイルをzip化してアップロード（`CreateZipUploadConfigSourceDetails`）
- スタックIDをセッションに紐付けて永続化
- `terraform_version = "1.5.x"` を指定

### 4. ジョブステータス取得

- `get_rm_job_status`でジョブの進行状況とログを取得
- `get_job_logs`でTerraformの出力ログを取得

## 受け入れ条件

### IaCテンプレート生成
- [ ] 生成される変数名が`compartment_ocid`（RM自動入力対応）
- [ ] providerブロックにauthパラメータが含まれない
- [ ] `tenancy_ocid`変数が宣言される

### RM経由のTerraform実行
- [ ] `run_terraform_plan`がRMのPlanジョブを作成し、完了まで待機して結果を返す
- [ ] `run_terraform_apply`がRMのApplyジョブを作成し、完了まで待機して結果を返す
- [ ] `run_terraform_destroy`がRMのDestroyジョブを作成し、完了まで待機して結果を返す
- [ ] 各ツールの返却値（TerraformResult）の形式が変わらない（LLM側の互換性維持）

### RMスタック管理
- [ ] セッションごとにRMスタックが作成される
- [ ] Terraformファイルがzip化されてRMにアップロードされる
- [ ] 自動入力変数（region, compartment_ocid）はvariablesに渡さなくてよい
- [ ] ユーザー指定変数（subnet_idなど自動入力でない変数）のみ渡す

### ジョブステータス
- [ ] `get_rm_job_status`がジョブの状態とログを返す

## 成功指標

- mcp-gaugeでリモートE2Eテスト（plan → apply → destroy）がエラー0で完走する
- `update_terraform_file`不要で認証が自動処理される
- ユーザーがregionやcompartment_idを手動指定する必要がない

## スコープ外

- RM Driftの検出
- 複数環境（dev/staging/prod）のスタック管理
- スタックの手動削除ツール
- schema.yamlの生成（将来拡張）

## 参照ドキュメント

- `docs/functional-design.md` - RMStack/RMJobモデル定義
- `docs/architecture.md` - インフラレイヤー仕様
- OCI Resource Manager API: https://docs.oracle.com/iaas/api/#/en/resourcemanager/
- RM自動入力変数: https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Concepts/terraformconfigresourcemanager.htm
- OCI Python SDK ResourceManagerClient: https://docs.oracle.com/en-us/iaas/tools/python/latest/api/resource_manager/client/oci.resource_manager.ResourceManagerClient.html
