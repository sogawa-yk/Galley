# Integration Test Instructions

## Purpose
Skills/Workflows間の連携とPythonモジュール間の統合をテストする。

## Test Scenarios

### Scenario 1: Hearing → TF Generation 連携
- **Description**: hearing/result.json が generate-terraform Skill の入力として正しく機能するか
- **Setup**: テスト用result.jsonを配置
- **Test Steps**:
  1. `artifacts/tests/test_hearing/expected_result_ecommerce.json` を `hearing/result.json` としてコピー
  2. generate-terraform Skill をClaude Code（テストエージェント）で実行
  3. `generated/ecommerce-demo/terraform/` に生成されたファイルを確認
- **Expected Results**: provider.tf, variables.tf, network.tf, compute.tf, database.tf, lb.tf, outputs.tf が生成
- **Cleanup**: generated/ ディレクトリを削除

### Scenario 2: TF Generation → Infra Deployment 連携
- **Description**: 生成されたTerraformが正しくzip化・Stack作成できるか
- **Setup**: Scenario 1の出力を入力として使用
- **Test Steps**:
  1. `artifacts/src/oci_rm.py` の `zip_terraform_dir()` で `generated/ecommerce-demo/terraform/` をzip化
  2. zipの構造（フラット、.tfファイル含む）を確認
- **Expected Results**: terraform.zip が生成、フラット構造、全.tfファイル含む
- **Note**: 実際のStack作成はOCI環境が必要（統合テスト環境でのみ実行可能）

### Scenario 3: Deploy → Verify 連携
- **Description**: endpoints.json が verify Skill の入力として正しく機能するか
- **Setup**: テスト用endpoints.jsonを配置
- **Test Steps**:
  1. `artifacts/src/deployer.py` の `save_endpoints()` でendpoints.jsonを生成
  2. `artifacts/src/e2e_runner.py` の `health_check()` で生成されたURLにアクセス（モック）
- **Expected Results**: endpoints.jsonのURLが正しくe2e_runnerに渡される

### Scenario 4: 全体ワークフロー（エージェント分離テスト — DC-5）
- **Description**: build-demo-env.md Workflowの全フェーズが正しく連携するか
- **Setup**: テスト用ワークスペース + Claude Code Skills/Workflows配置
- **Test Steps**:
  1. **開発エージェント**: artifacts/ のファイルをテスト環境にコピー
  2. **テストエージェント**: build-demo-env Workflowを実行（サンプル要望入力）
  3. **評価エージェント**: 各フェーズの出力ファイルを検証
- **Expected Results**: hearing/ → generated/{name}/terraform/ → app/ → stack_outputs.json → endpoints.json → test_results.json → summary.md の全ファイルが生成
- **Note**: OCI環境が必要（Phase 2以降の実Infrastructure操作）

## Run Integration Tests

### ローカル統合テスト（OCI不要）
```bash
cd artifacts
# Scenario 1-3のファイル連携テスト
uv run python -c "
from src.oci_rm import zip_terraform_dir
from src.deployer import save_endpoints
from src.e2e_runner import generate_report
from src.reporter import generate_summary
import tempfile, os, json

# Test zip
d = tempfile.mkdtemp()
with open(os.path.join(d, 'main.tf'), 'w') as f: f.write('resource \"null\" \"test\" {}')
zip_path = zip_terraform_dir(d)
assert os.path.exists(zip_path)

# Test endpoints
ep_path = os.path.join(d, 'endpoints.json')
save_endpoints('http://test:8080', 'test', 'oke', ep_path)
with open(ep_path) as f: ep = json.load(f)
assert ep['health_url'] == 'http://test:8080/health'

# Test report
report_path = os.path.join(d, 'report.md')
generate_report({'total': 1, 'passed': 1, 'failed': 0, 'results': [{'name': 'test', 'passed': True, 'response_time_ms': 50, 'error': None}]}, report_path)
assert os.path.exists(report_path)

# Test summary
summary_path = os.path.join(d, 'summary.md')
generate_summary('test', 'ocid1.stack.x', ep, {'total': 1, 'passed': 1}, summary_path)
assert os.path.exists(summary_path)

print('All integration tests passed!')
"
```

### OCI環境統合テスト（Scenario 4）
OCI環境でのフルワークフローテストは、実際のインスタンスプリンシパル認証環境で実施。
手順はScenario 4を参照。
