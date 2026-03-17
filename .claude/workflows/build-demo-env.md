# Build Demo Environment Workflow

## Description
プリセールスエンジニアの要望から、OCI上のデモ環境を完全自動で構築するメインオーケストレーターWorkflowです。

## データフロー

```
hearing → hearing/result.json
generate-terraform → generated/{project_name}/terraform/
deploy-infra → generated/{project_name}/stack_outputs.json
generate-app → generated/{project_name}/app/
deploy-app → generated/{project_name}/endpoints.json
verify → generated/{project_name}/test_results.json
```

## Steps

### Step 1: ヒアリング
Hearing Skillを実行して、ユーザーの要望を収集します。

Use skill: hearing

ヒアリングが完了したら次のステップに進みます。

**エラーゲート**: このステップが失敗した場合、以降のステップは実行せず、エラー内容をユーザーに報告してください。

---

### Step 2: Terraformコード生成
ヒアリング結果に基づいてTerraformコードを生成します。

Use skill: generate-terraform

**エラーゲート**: このステップが失敗した場合、以降のステップは実行せず、エラー内容をユーザーに報告してください。

---

### Step 3: アプリケーション生成
アプリケーションコードの生成とテストを行います。

Use skill: generate-app

**エラーゲート**: このステップが失敗した場合、以降のステップは実行せず、エラー内容をユーザーに報告してください。

---

### Step 4: インフラ構築
Resource ManagerでTerraformをapplyします。

Use skill: deploy-infra

**エラーゲート**: このステップが失敗した場合、以降のステップは実行せず、エラー内容をユーザーに報告してください。部分的に作成されたリソースがある場合は、クリーンアップ方法を案内してください（OCI Console > Resource Manager > Stacks > Destroy）。

---

### Step 5: アプリケーションデプロイ
インフラ上にアプリケーションをデプロイします。

Use skill: deploy-app

**エラーゲート**: このステップが失敗した場合、以降のステップは実行せず、エラー内容をユーザーに報告してください。部分的に作成されたリソースがある場合は、クリーンアップ方法を案内してください。

---

### Step 6: 動作確認
デプロイしたアプリケーションのE2Eテストを実行します。

Use skill: verify

**エラーゲート**: このステップが失敗した場合、以降のステップは実行せず、エラー内容をユーザーに報告してください。部分的に作成されたリソースがある場合は、クリーンアップ方法を案内してください。

---

### Step 7: 最終レポート生成

以下のPythonコードでサマリーを生成してください:

```python
import json
from src.reporter import generate_summary

# Load data
with open(f"hearing/result.json") as f:
    result = json.load(f)
project_name = result["project_name"]

with open(f"generated/{project_name}/stack_outputs.json") as f:
    stack_outputs = json.load(f)

with open(f"generated/{project_name}/endpoints.json") as f:
    endpoints = json.load(f)

with open(f"generated/{project_name}/test_results.json") as f:
    test_results = json.load(f)

# Generate summary
generate_summary(
    project_name=project_name,
    stack_id=stack_outputs.get("_stack_id", "N/A"),
    endpoints=endpoints,
    test_results=test_results,
    output_path=f"generated/{project_name}/summary.md",
)
```

最終レポートをユーザーに表示してください:

```
============================================
  デモ環境構築が完了しました！
============================================

プロジェクト: {project_name}
アプリケーションURL: {url}
ヘルスチェック: {health_url}

テスト結果: {passed}/{total} passed

Stack OCID: {stack_id}

環境を削除する場合:
  OCI Console > Resource Manager > Stacks
  > "{project_name}-stack" > Destroy

詳細: generated/{project_name}/summary.md
============================================
```
