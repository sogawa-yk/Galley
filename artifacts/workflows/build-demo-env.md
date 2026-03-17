# Build Demo Environment Workflow

## Description
プリセールスエンジニアの要望から、OCI上のデモ環境を完全自動で構築するメインオーケストレーターWorkflowです。

## Steps

### Step 1: ヒアリング
Hearing Skillを実行して、ユーザーの要望を収集します。

Use skill: hearing

ヒアリングが完了したら次のステップに進みます。

---

### Step 2: Terraformコード生成
ヒアリング結果に基づいてTerraformコードを生成します。

Use skill: generate-terraform

---

### Step 3: 並行実行 — インフラ構築 + アプリ生成

**以下の2つを並行で実行してください:**

#### 3a: インフラ構築（バックグラウンド）
Resource ManagerでTerraformをapplyします。これは時間がかかります。

Use skill: deploy-infra

（バックグラウンドエージェントとして実行）

**並列実行が不可能な場合の代替フロー:**
ランタイムがバックグラウンドエージェントをサポートしない場合は、以下の順序で逐次実行してください:
1. generate-app（アプリ生成・テスト）を先に実行
2. deploy-infra（インフラ構築）を実行
この順序により、インフラ構築の待ち時間中にアプリ生成を済ませる並列実行の利点を最大限再現します。

#### 3b: アプリケーション生成（フォアグラウンド）
インフラ構築を待たずに、アプリケーションコードの生成とテストを行います。

Use skill: generate-app

---

### Step 4: 並行実行の完了待ち
Step 3a（インフラ構築）と Step 3b（アプリ生成）の両方が完了するのを待ちます。

両方が完了したら次のステップに進みます。

---

### Step 5: アプリケーションデプロイ
インフラ上にアプリケーションをデプロイします。

Use skill: deploy-app

---

### Step 6: 動作確認
デプロイしたアプリケーションのE2Eテストを実行します。

Use skill: verify

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
