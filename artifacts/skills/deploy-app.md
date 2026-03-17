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

**Functions の場合**: Phase 2, Phase 2.5, Phase 3 をスキップし、直接 Phase 3.5 に進んでください（fn deploy がビルド・プッシュを内部処理します）。

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

### Phase 2.5: OCIR認証

OCIRへのpush前に認証が必要です:

```python
from src.deployer import login_to_ocir

region = get_region()
namespace = get_tenancy_namespace()

login_to_ocir(
    region=region,
    tenancy_namespace=namespace,
    username="oracleidentitycloudservice/{user_email}",
    auth_token=auth_token,
)
```

認証トークンが未設定の場合、ユーザーにOCI Auth Tokenを質問してください。手動で実行する場合:

```bash
docker login {region}.ocir.io -u {tenancy_namespace}/oracleidentitycloudservice/{user_email} -p {auth_token}
```

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

stack_outputsからアプリケーション環境変数を構成します。データベース種別に応じて接続情報の形式が異なります:

**ATP (Autonomous Database) の場合:**
- `DB_CONNECTION_STRING`: stack_outputsの`db_connection_string`をそのまま使用（TNS形式）
- ATPはウォレットベース接続のため、host/port分解は不要

**MySQL の場合:**
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` を個別に設定
- `DB_CONNECTION_STRING`: `mysql://{user}:{password}@{host}:{port}/{db_name}` 形式で構築

**共通環境変数:**
- `PORT`: "8080"
- `APP_ENV`: "production" (※ NODE_ENVではなく汎用的な変数名を使用)
- `DB_CONNECTION_STRING`: 上記のDB種別に応じた値

**言語固有の環境変数:**
- Node.js: `NODE_ENV: "production"` を追加（Express等のFWが参照するため）
- Python: `PYTHONUNBUFFERED: "1"` を追加（ログ出力のバッファリング防止）

```python
import json

# hearing/result.jsonからdatabase種別を取得
with open("hearing/result.json") as f:
    hearing = json.load(f)
db_type = hearing.get("database", {}).get("type", "")

if db_type == "atp":
    # ATP: TNS接続文字列をそのまま使用
    db_connection_string = stack_outputs.get("db_connection_string", "")
    env_vars = {
        "PORT": "8080",
        "APP_ENV": "production",
        "DB_CONNECTION_STRING": db_connection_string,
    }
elif db_type == "mysql":
    # MySQL: 個別の接続パラメータ
    db_host = stack_outputs.get("db_host", "")
    db_port = stack_outputs.get("db_port", "3306")
    db_user = stack_outputs.get("db_user", "admin")
    db_password = stack_outputs.get("db_password", "")
    db_name = project_name.replace("-", "_")
    db_connection_string = f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    env_vars = {
        "PORT": "8080",
        "APP_ENV": "production",
        "DB_HOST": db_host,
        "DB_PORT": db_port,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
        "DB_NAME": db_name,
        "DB_CONNECTION_STRING": db_connection_string,
    }
else:
    # DBなし
    env_vars = {
        "PORT": "8080",
        "APP_ENV": "production",
    }
```

**DB_PASSWORDの取得**: stack_outputsにパスワードが含まれない場合（Terraform sensitive）、`generated/{project_name}/terraform/terraform.tfvars`から`db_admin_password`を読み取る

**注意**: 各デプロイパス（Phase 4）では、ここで構成した `env_vars` を環境変数としてコンテナに渡してください。

---

### Phase 4: デプロイ（自己修正ループ、最大2回リトライ）

`compute_type` に応じて適切なデプロイ方式を選択してください:

#### OKE の場合:
1. kubeconfig を stack_outputs["oke_kubeconfig"] から取得（base64エンコード）
2. デコードしてファイルに保存:
```python
import base64
kubeconfig_b64 = stack_outputs["oke_kubeconfig"]
with open("kubeconfig.yaml", "w") as f:
    f.write(base64.b64decode(kubeconfig_b64).decode())
```
3. Kubernetes manifests (Deployment, Service, Ingress) を動的生成
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
2. SSH接続（ユーザー: `opc`、OCIデフォルト）
3. OCIR認証: `docker login {region}.ocir.io -u {tenancy_namespace}/oracleidentitycloudservice/{user_email} -p {auth_token}`
4. イメージ取得: `docker pull {ocir_url}`
5. コンテナ起動: `docker run -d --name {project_name} -p 8080:8080 {env_vars各キーを-eオプションで} {ocir_url}`

**SSH鍵について**: generate-terraformが`var.ssh_public_key`でCompute Instanceに公開鍵を設定。対応する秘密鍵のパスをユーザーに確認してください。

```python
import subprocess

compute_ip = stack_outputs["compute_public_ip"]
# SSH鍵パスをユーザーに確認
# ssh_key_path = ユーザーから取得

# OCIR認証（Compute上で実行）
ssh_prefix = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no opc@{compute_ip}"
subprocess.run(f"{ssh_prefix} 'docker login {region}.ocir.io -u {namespace}/oracleidentitycloudservice/{{user_email}} -p {{auth_token}}'", shell=True, check=True)

# イメージ取得と起動
subprocess.run(f"{ssh_prefix} 'docker pull {ocir_url}'", shell=True, check=True)
env_flags = " ".join(f"-e {k}={v}" for k, v in env_vars.items())
subprocess.run(f"{ssh_prefix} 'docker run -d --name {project_name} -p 8080:8080 {env_flags} {ocir_url}'", shell=True, check=True)

endpoint_url = f"http://{compute_ip}:8080"
resource_id = stack_outputs.get("compute_instance_id", "")
```

#### Functions の場合:
**注意**: Functions では `fn deploy` がイメージのビルド・プッシュを内部で処理するため、Phase 2（イメージビルド）とPhase 3（OCIRプッシュ）はスキップしてください。

1. `func.yaml` の `config:` セクションに環境変数を書き込む:
```python
import yaml
func_yaml_path = f"generated/{project_name}/app/func.yaml"
with open(func_yaml_path) as f:
    func_config = yaml.safe_load(f)
func_config.setdefault("config", {}).update(env_vars)
with open(func_yaml_path, "w") as f:
    yaml.dump(func_config, f)
```

2. fn CLIでデプロイ（`--app` にはアプリ名を使用、OCIDではない）:
```python
from src.deployer import deploy_to_functions
result = deploy_to_functions(
    app_dir=f"generated/{project_name}/app",
    app_name=project_name,  # アプリ名を使用（OCIDではない）
    function_name=project_name,
)
```

3. エンドポイント解決:
```python
# API Gatewayがある場合はそのURLを使用
if stack_outputs.get("api_gateway_url"):
    endpoint_url = stack_outputs["api_gateway_url"]
else:
    # Functions invoke endpoint（OCI SDK認証が必要）
    endpoint_url = stack_outputs.get("functions_invoke_endpoint", f"https://functions.{region}.oci.oraclecloud.com")
resource_id = stack_outputs.get("functions_app_id", "")
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

2. **エンドポイント解決（優先順位付き）:**

```python
# エンドポイント解決の優先順位:
# 1. API Gateway URL（Functions + APIGW シナリオ）
# 2. LB Public IP（CI/Compute + LB シナリオ）
# 3. コンピュートリソースの直接IP
if stack_outputs.get("api_gateway_url"):
    endpoint_url = stack_outputs["api_gateway_url"]
elif stack_outputs.get("lb_public_ip"):
    endpoint_url = f"http://{stack_outputs['lb_public_ip']}"
```
API GatewayもLBも存在しない場合のみ、コンピュートリソースの直接IPを使用してください。

3. エンドポイントURLを確定し、endpoints.jsonを出力:

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

2. **スキーマ初期化**: compute_typeと言語に応じた方法で実行:

**シードコマンドの決定**（`hearing/result.json`の`language`フィールドを参照）:

| 言語 | シードコマンド |
|------|----------------|
| Python | `python -m seed` or `python seed.py` |
| Node.js | `npm run seed` |

**OKE の場合**:
```bash
# Kubernetes Jobでマイグレーション実行（シードコマンドは言語に応じて変更）
kubectl --kubeconfig=kubeconfig.yaml run db-init \
  --image={ocir_url} \
  --restart=Never \
  --env="DB_CONNECTION_STRING={db_connection_string}" \
  --command -- {seed_command}
kubectl --kubeconfig=kubeconfig.yaml wait --for=condition=Complete job/db-init --timeout=120s
```

**Container Instances / Compute の場合**:
アプリケーション起動時に自動的にテーブル作成とシードを実行するよう、generate-appスキルで生成されたアプリのエントリーポイントに初期化ロジックが含まれていることを確認してください。含まれていない場合は、SSH/execで上記の言語別シードコマンドを実行してください。

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
