# Deploy Application Skill

## Description
生成したアプリケーションをビルドし、OCIRにプッシュし、OCI上にデプロイするSkillです。

## Instructions

あなたはアプリケーションデプロイエージェントです。生成済みアプリケーションをOCI上にデプロイしてください。

**入力データ契約:**
- `hearing/result.json` 必須キー: `project_name`, `compute_type`
- `generated/{project_name}/stack_outputs.json`: deploy-infra Skillで生成（Terraform outputs + `_stack_id`メタデータ）
- `generated/{project_name}/app/Dockerfile`: generate-app Skillで生成

**前提**: Unit 3（Infra Deploy）と Unit 4（App Generation）が両方完了していること。

以下のフェーズを順番に実行してください。

---

### Phase 1: 情報収集

1. `hearing/result.json` から `project_name`, `compute_type` を取得:

```python
import json

with open("hearing/result.json") as f:
    result = json.load(f)
project_name = result["project_name"]
compute_type = result["compute_type"]
```

2. `generated/{project_name}/stack_outputs.json` を読み込み、インフラ情報を取得:

```python
with open(f"generated/{project_name}/stack_outputs.json") as f:
    stack_outputs = json.load(f)
```

3. `generated/{project_name}/app/Dockerfile` の存在を確認

4. コンパートメントIDを解決（Container Instances/Functionsデプロイに必要）:

```python
from src.oci_cli import get_compartment_id

try:
    compartment_id = get_compartment_id()
except RuntimeError:
    # ユーザーにコンパートメントIDを質問してください
    pass
```

---

### Phase 2: コンテナイメージビルド

```python
from src.deployer import build_image

image = build_image(
    app_dir=f"generated/{project_name}/app",
    image_name=project_name,
)
print(f"Built: {image}")
```

ビルド失敗時: Dockerfileを修正して再ビルド（最大2回）

---

### Phase 3: OCIRプッシュ

```python
from src.deployer import push_to_ocir, get_tenancy_namespace
from src.oci_cli import get_region

region = get_region()
namespace = get_tenancy_namespace()

ocir_url = push_to_ocir(
    image_name=image,  # build_imageの戻り値を使用
    region=region,
    tenancy_namespace=namespace,
    repo_name=project_name,
)
print(f"Pushed: {ocir_url}")
```

---

### Phase 3.5: 環境変数の準備

デプロイ先のアプリケーションに渡す環境変数を `stack_outputs` から構成します:

```python
# DB接続情報の構成（database使用時）
db_host = stack_outputs.get("db_host", "")
db_port = stack_outputs.get("db_port", "3306")
db_user = stack_outputs.get("db_user", "admin")
db_password = stack_outputs.get("db_password", "")  # Terraform変数から取得が必要
db_name = project_name.replace("-", "_")

# DB_CONNECTION_STRINGの構築
if db_host:
    db_connection_string = f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
else:
    db_connection_string = ""

env_vars = {
    "PORT": "8080",
    "NODE_ENV": "production",
    "DB_HOST": db_host,
    "DB_PORT": db_port,
    "DB_USER": db_user,
    "DB_PASSWORD": db_password,
    "DB_NAME": db_name,
    "DB_CONNECTION_STRING": db_connection_string,
}
```

**DB_PASSWORDの取得**: `stack_outputs` にDB passwordが含まれない場合（Terraformのsensitive出力のため）、以下の方法で取得してください:
1. `terraform.tfvars` から `db_admin_password` を読み取る
2. または、ユーザーにパスワードを質問する

**注意**: 各デプロイパス（Phase 4）では、ここで構成した `env_vars` を環境変数としてコンテナに渡してください。

---

### Phase 4: デプロイ（自己修正ループ、最大2回リトライ）

`compute_type` に応じて適切なデプロイ方式を選択してください:

#### OKE の場合:
1. kubeconfig を stack_outputs から取得・ファイル保存
2. Kubernetes manifests (Deployment, Service, Ingress) を動的生成
   - image: OCIRのURL
   - port: 8080
   - replicas: 1
   - health check: `/health`
   - Kubernetes Deploymentのspec.containers.envに`env_vars`を設定
3. デプロイ:
```python
from src.deployer import deploy_to_oke
deploy_to_oke(kubeconfig_path="kubeconfig.yaml", manifests_dir="k8s/")
```
4. Service の External IP を取得してエンドポイントURLとする
```python
# external_ip は kubectl get svc から取得
endpoint_url = f"http://{external_ip}:8080"
resource_id = "oke-deployment"
```

#### Container Instances の場合:
```python
from src.deployer import deploy_to_container_instances
result = deploy_to_container_instances(
    compartment_id=compartment_id,
    image_url=ocir_url,
    display_name=f"{project_name}-app",
    subnet_id=stack_outputs["public_subnet_id"],
)
endpoint_url = f"http://{result['public_ip']}:8080"
resource_id = result["id"]
# env_varsはcontainer_instance作成時にenvironment_variables引数で渡す
```

#### Compute の場合:
1. stack_outputs から `compute_public_ip` を取得
2. SSH で接続し docker pull + docker run
   - SSH接続後、docker run時に`-e`オプションで`env_vars`の各キーを渡す
```python
endpoint_url = f"http://{stack_outputs['compute_public_ip']}:8080"
resource_id = stack_outputs.get("compute_instance_id", "")
```

#### Functions の場合:
```python
from src.deployer import deploy_to_functions
deploy_to_functions(
    app_dir=f"generated/{project_name}/app",
    function_app_id=stack_outputs["functions_app_id"],
    function_name=project_name,
)
endpoint_url = stack_outputs.get("functions_invoke_endpoint", "")
resource_id = stack_outputs.get("functions_app_id", "")
# func.yamlのconfigフィールドに`env_vars`を設定
```

**デプロイ失敗時**: エラー分析 → 設定/manifests修正 → 再デプロイ（最大2回）

---

### Phase 5: デプロイ完了確認 + endpoints.json出力

1. Phase 4で取得した `endpoint_url` と `resource_id` を使用してデプロイ完了を待機:

```python
from src.deployer import wait_for_deployment

# endpoint_url と resource_id は Phase 4 の各デプロイパスで設定済み
wait_for_deployment(deploy_type=compute_type, resource_id=resource_id)
```

2. エンドポイントURLを確定し、endpoints.jsonを出力:

```python
from src.deployer import save_endpoints

save_endpoints(
    url=endpoint_url,
    project_name=project_name,
    compute_type=compute_type,
    output_path=f"generated/{project_name}/endpoints.json",
)
```

---

### Phase 6: DB初期化（データベース使用時のみ）

デプロイしたアプリケーションのデータベーススキーマを初期化し、サンプルデータを投入します。

1. `hearing/result.json` の `database` フィールドを確認。`database` が存在しない場合はこのPhaseをスキップ。

2. **スキーマ初期化**: compute_typeに応じた方法で実行:

**OKE の場合**:
```bash
# Kubernetes Jobでマイグレーション実行
kubectl --kubeconfig=kubeconfig.yaml run db-init \
  --image={ocir_url} \
  --restart=Never \
  --env="DB_HOST={db_host}" \
  --env="DB_USER={db_user}" \
  --env="DB_PASSWORD={db_password}" \
  --env="DB_NAME={db_name}" \
  --command -- npm run seed
kubectl --kubeconfig=kubeconfig.yaml wait --for=condition=Complete job/db-init --timeout=120s
```

**Container Instances / Compute の場合**:
アプリケーション起動時に自動的にテーブル作成とシードを実行するよう、generate-appスキルで生成されたアプリのエントリーポイントに初期化ロジックが含まれていることを確認してください。含まれていない場合は、SSH/execで `npm run seed` を実行してください。

3. 完了確認: ヘルスチェックを再実行して正常動作を確認。

---

### 完了報告

```
アプリケーションをデプロイしました。
- デプロイ先: {compute_type}
- エンドポイント: {endpoint_url}
- ヘルスチェック: {endpoint_url}/health
- DB初期化: {実行した場合: 完了 / スキップ}
- endpoints.json: generated/{project_name}/endpoints.json

次のフェーズ（動作確認）に進む準備ができました。
```
