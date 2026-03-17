# Verify Skill

## Description
デプロイしたアプリケーションのE2Eテストと動作確認を実行するSkillです。

## Instructions

あなたは品質検証エージェントです。デプロイ済みアプリケーションの動作確認を行ってください。

**入力データ契約:**
- `hearing/result.json` 必須キー: `project_name`
- `generated/{project_name}/endpoints.json`: deploy-app Skillで生成（`url`, `health_url`, `compute_type`, `project_name`キー）

---

### Phase 1: 情報収集

1. `hearing/result.json` から `project_name` を取得:

```python
import json

with open("hearing/result.json") as f:
    result = json.load(f)
project_name = result["project_name"]
```

2. `generated/{project_name}/endpoints.json` を読み込み、エンドポイント情報を取得:

```python
with open(f"generated/{project_name}/endpoints.json") as f:
    endpoints = json.load(f)
base_url = endpoints["url"]
```

---

### Phase 2: ヘルスチェック

```python
from src.e2e_runner import health_check

result = health_check(
    url=endpoints["health_url"],
    timeout=30,
    retries=10,
    interval=10,
)
print(f"Health check: {'PASS' if result['passed'] else 'FAIL'}")
```

ヘルスチェック失敗時: デプロイ状態を確認し、問題を報告

---

### Phase 3: 機能テスト

1. `hearing/result.json` のアプリ要件から、テストすべきAPIエンドポイントを特定
2. テストスペックを構築:

```python
test_specs = [
    {"name": "Health Check", "url": f"{base_url}/health", "expected_status": 200},
    # アプリの機能に応じて追加
    # {"name": "GET /api/items", "url": f"{base_url}/api/items", "expected_status": 200},
    # {"name": "POST /api/items", "url": f"{base_url}/api/items", "method": "POST", "payload": {...}},
]
```

**認証が必要なエンドポイントのテスト方法:**

アプリケーションが認証機能を持つ場合（`hearing/result.json` の `custom_requirements` を確認）、以下の手順でセッションを取得してからテストしてください:

1. まず認証エンドポイントにログインリクエストを送信:
```python
import requests
session = requests.Session()

# サンプルユーザーでログイン（generate-appのseedデータを使用）
login_response = session.post(
    f"{base_url}/auth/login",
    data={"username": "admin", "password": "password123"},
    allow_redirects=False,
)
```

2. ログイン後のセッションを使って認証済みエンドポイントをテスト:
```python
# セッション付きリクエスト
test_specs_authenticated = [
    {"name": "Dashboard", "url": f"{base_url}/dashboard", "expected_status": 200, "session": session},
    {"name": "Tasks List", "url": f"{base_url}/tasks", "expected_status": 200, "session": session},
]
```

3. `run_test_suite` はセッションオブジェクトをサポートしていない場合、個別に `session.get()` でテストしてレポートに結果を追加してください。

3. テスト実行:
```python
from src.e2e_runner import run_test_suite

results = run_test_suite(test_specs)
print(f"Results: {results['passed']}/{results['total']} passed")
```

---

### Phase 4: レポート生成

```python
from src.e2e_runner import generate_report

report_path = generate_report(
    test_results=results,
    output_path=f"generated/{project_name}/test_results.md",
)
```

テスト結果をJSONでも保存:
```python
import json
with open(f"generated/{project_name}/test_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

---

### Phase 5: 結果報告

```
E2Eテスト完了:
- ヘルスチェック: {PASS/FAIL}
- 機能テスト: {passed}/{total} passed
- レポート: generated/{project_name}/test_results.md

{失敗テストがある場合はその詳細}
```
