# Deploy Infrastructure Skill

## Description
OCI Resource Managerを使用して、生成済みTerraformコードからインフラストラクチャを構築するSkillです。
自己修正ループにより、Plan/Apply失敗時にも自動でコードを修正して再試行します。

## Instructions

あなたはOCIインフラ構築エージェントです。生成済みのTerraformコードをOCI Resource Managerで適用し、インフラを構築してください。

**入力データ契約:**
- `hearing/result.json` 必須キー: `project_name`
- `generated/{project_name}/terraform/` ディレクトリ: generate-terraform Skillで生成済み

以下のフェーズを順番に実行してください。

---

### Phase 1: 準備

1. `hearing/result.json` からproject_nameを読み取ります:

```python
import json
with open("hearing/result.json") as f:
    result = json.load(f)
project_name = result["project_name"]
```
2. `generated/{project_name}/terraform/` ディレクトリの存在を確認します
3. コンパートメントIDを解決します。以下のPythonコードを実行してください:

```python
from src.oci_cli import get_compartment_id, get_region

try:
    compartment_id = get_compartment_id()
    print(f"Compartment ID: {compartment_id}")
except RuntimeError as e:
    print(f"自動解決失敗: {e}")
    # ユーザーにコンパートメントIDを質問してください
```

4. コンパートメントIDが自動解決できない場合、ユーザーに質問してください:
   「コンパートメントOCIDを教えてください（例: ocid1.compartment.oc1..xxx）」

5. リージョンも同様に解決します:

```python
try:
    region = get_region()
except RuntimeError:
    # ユーザーにリージョンを質問
```

6. `terraform.tfvars` のPLACEHOLDER値を解決済みの値で更新します。terraform.tfvars内の `compartment_id = "PLACEHOLDER"` と `region = "PLACEHOLDER"` を解決済みの値で更新してください。

---

### Phase 2: Stack作成 + Plan + Apply（自己修正ループ）

**リトライ仕様**: Plan失敗は最大2回リトライ、Apply失敗も最大2回リトライ（それぞれ独立カウント）。Apply失敗の自己修正ループでPlanを再実行する場合、そのPlan失敗はApplyリトライカウントに含める（Planリトライカウントは消費しない）。同一エラーが2回連続した場合は即座にユーザーに報告して停止。

#### 2.1: Stack作成

```python
from src.oci_rm import create_stack

stack_id = create_stack(
    compartment_id=compartment_id,
    terraform_dir=f"generated/{project_name}/terraform",
    display_name=f"{project_name}-stack",
)
print(f"Stack created: {stack_id}")
```

#### 2.2: Plan実行

```python
from src.oci_rm import run_plan, wait_for_job, get_job_logs

plan_job_id = run_plan(stack_id)
print(f"Plan job started: {plan_job_id}")

plan_result = wait_for_job(plan_job_id, timeout=3600, interval=30)
```

#### 2.3: Plan結果確認

```python
if plan_result["lifecycle_state"] == "SUCCEEDED":
    # Apply実行へ (Phase 2.4)
    pass
elif plan_result["lifecycle_state"] == "FAILED":
    # 自己修正ループ
    logs = get_job_logs(plan_job_id)
    # エラー分析・修正...
elif plan_result["lifecycle_state"] == "CANCELED":
    # ユーザーに報告して停止
    pass
```

**Plan成功の場合**: Apply実行（2.4へ）

**Planキャンセルの場合**: ユーザーに報告して停止

**Plan失敗の場合（自己修正ループ）**:
1. ログを取得:
```python
logs = get_job_logs(plan_job_id)
```
2. エラー内容を分析してください
3. Terraformコードを修正してください（`generated/{project_name}/terraform/` 内のファイル）
4. 修正後、以下を実行して再試行:
```python
from src.oci_rm import create_stack

# Stackを更新（create_stackが内部でzip化を実行、既存Stack検出時は自動更新）
stack_id = create_stack(
    compartment_id=compartment_id,
    terraform_dir=f"generated/{project_name}/terraform",
    display_name=f"{project_name}-stack",
)
# Phase 2.2 に戻って Plan 再実行
```
5. 最大2回のリトライ後も失敗する場合、エラー内容をユーザーに報告して停止

#### 2.4: Apply実行

```python
from src.oci_rm import run_apply

apply_job_id = run_apply(stack_id)
print(f"Apply job started: {apply_job_id}")

apply_result = wait_for_job(apply_job_id, timeout=3600, interval=30)
```

#### 2.5: Apply結果確認

```python
if apply_result["lifecycle_state"] == "SUCCEEDED":
    # Phase 3へ
    pass
elif apply_result["lifecycle_state"] == "FAILED":
    # 自己修正ループ
    logs = get_job_logs(apply_job_id)
    # エラー分析・修正...
elif apply_result["lifecycle_state"] == "CANCELED":
    # ユーザーに報告して停止
    pass
```

**Apply成功の場合**: Phase 3へ

**Applyキャンセルの場合**: ユーザーに報告して停止

**Apply失敗の場合（自己修正ループ）**:
1. ログを取得:
```python
logs = get_job_logs(apply_job_id)
```
2. エラー内容を分析してください
3. Terraformコードを修正してください
4. 修正後:
```python
from src.oci_rm import create_stack

# Stackを更新（create_stackが内部でzip化を実行、既存Stack検出時は自動更新）
stack_id = create_stack(
    compartment_id=compartment_id,
    terraform_dir=f"generated/{project_name}/terraform",
    display_name=f"{project_name}-stack",
)
# Phase 2.2 に戻って Plan → Apply 再実行
```
5. 部分的に作成されたリソースはTerraform stateが管理しているため、修正後のApplyで差分のみ適用されます
6. 最大2回のリトライ後も失敗する場合、エラー内容をユーザーに報告して停止

---

### Phase 3: 結果取得

1. Stack Outputsを取得:

```python
from src.oci_rm import get_stack_outputs, save_stack_outputs

outputs = get_stack_outputs(stack_id, apply_job_id)
save_stack_outputs(
    outputs=outputs,
    stack_id=stack_id,
    job_id=apply_job_id,
    project_name=project_name,
    output_path=f"generated/{project_name}/stack_outputs.json",
)
```

2. ユーザーに完了を報告:

```
インフラ構築が完了しました。
- Stack OCID: {stack_id}
- Stack名: {project_name}-stack
- 出力ファイル: generated/{project_name}/stack_outputs.json
- 主要リソース: [作成されたリソースの概要]

環境を削除する場合は、OCI Console > Resource Manager > Stacks から
「{project_name}-stack」を選択し、Destroyを実行してください。
```

---

### タイムアウト時の対応

`TimeoutError` が発生した場合:
- 現在のJob状態をユーザーに報告
- OCI ConsoleのResource Manager画面でJobの状態を確認するよう案内
- Jobは継続実行中の可能性があるため、キャンセルはユーザー判断に委ねる
