# Component Methods

## Python Core Modules

### C-8: oci_rm.py (OCI Resource Manager Module)

```python
def create_stack(compartment_id: str, terraform_dir: str, display_name: str) -> str:
    """TerraformディレクトリをzipしてResource Manager Stackを作成する。Stack OCIDを返す。"""

def run_plan(stack_id: str) -> str:
    """Stack上でPlan Jobを実行する。Job OCIDを返す。"""

def run_apply(stack_id: str) -> str:
    """Stack上でApply Jobを実行する。Job OCIDを返す。"""

def run_destroy(stack_id: str) -> str:
    """Stack上でDestroy Jobを実行する。Job OCIDを返す。"""

def get_job_status(job_id: str) -> dict:
    """Job のステータスを取得する。{status, time_finished, ...}を返す。"""

def wait_for_job(job_id: str, timeout: int = 1800, interval: int = 30) -> dict:
    """Jobが完了するまでポーリングする。最終ステータスを返す。"""

def get_job_logs(job_id: str) -> str:
    """Jobのログを取得する。"""

def get_stack_outputs(stack_id: str, job_id: str) -> dict:
    """Apply Job完了後のTerraform outputsを取得する。"""
```

### C-9: oci_cli.py (OCI CLI Wrapper)

```python
def run_command(args: list[str]) -> dict:
    """OCI CLIコマンドを実行し、JSON結果を返す。"""

def get_compartment_id() -> str:
    """現在のインスタンスのコンパートメントIDを取得する。"""

def get_region() -> str:
    """現在のリージョンを取得する。"""

def get_tenancy_id() -> str:
    """テナンシーIDを取得する。"""

def list_resources(resource_type: str, compartment_id: str) -> list[dict]:
    """指定タイプのリソース一覧を取得する。"""

def get_resource(resource_type: str, resource_id: str) -> dict:
    """指定リソースの詳細を取得する。"""
```

### C-10: deployer.py (Deployer Module)

```python
def build_image(app_dir: str, image_name: str, tag: str = "latest") -> str:
    """Dockerイメージをビルドする。イメージ名を返す。"""

def push_to_ocir(image_name: str, region: str, tenancy_namespace: str, repo_name: str) -> str:
    """OCIRにイメージをプッシュする。OCIR URLを返す。"""

def deploy_to_oke(kubeconfig: str, manifests_dir: str) -> dict:
    """OKEクラスターにkubectlでデプロイする。デプロイ結果を返す。"""

def deploy_to_container_instances(compartment_id: str, image_url: str, config: dict) -> dict:
    """Container Instancesにデプロイする。"""

def deploy_to_functions(compartment_id: str, app_dir: str, function_name: str) -> dict:
    """OCI Functionsにデプロイする。"""

def wait_for_deployment(deploy_type: str, resource_id: str, timeout: int = 600) -> dict:
    """デプロイ完了を待機する。"""
```

### C-11: e2e_runner.py (E2E Test Runner)

```python
def health_check(url: str, timeout: int = 30, retries: int = 10) -> dict:
    """ヘルスチェック（HTTP GET）を実行する。{status, response_time, ...}を返す。"""

def test_endpoint(url: str, method: str, payload: dict | None = None, expected_status: int = 200) -> dict:
    """APIエンドポイントをテストする。{passed, status_code, response, ...}を返す。"""

def run_test_suite(test_specs: list[dict]) -> dict:
    """テストスイートを実行する。{total, passed, failed, results}を返す。"""

def generate_report(test_results: dict, output_path: str) -> str:
    """テスト結果のMarkdownレポートを生成する。ファイルパスを返す。"""
```

### C-12: reporter.py (Reporter Module)

```python
def report_progress(phase: str, status: str, details: str, output_path: str) -> None:
    """フェーズ進捗をMarkdownレポートに追記する。"""

def generate_summary(project_name: str, stack_id: str, endpoints: list[str],
                     resources: list[dict], test_results: dict, output_path: str) -> str:
    """最終結果サマリーを生成する。ファイルパスを返す。"""

def report_error(phase: str, error: str, context: dict, output_path: str) -> None:
    """エラーレポートを出力する。"""
```

## Skill/Workflow Methods (Markdown)

Skills/Workflowsは自然言語の指示としてMarkdownに記述される。以下は各Skillの主要な処理ステップ。

### C-1: hearing.md
- ユーザー要望の受け取りと解析
- 質問リスト生成 → `hearing/questions.md` に出力
- 回答待ち → 回答検証 → 矛盾があれば追加質問
- 結果構造化 → `hearing/result.json` に出力

### C-2: generate-terraform.md
- `hearing/result.json` の読み込み
- OCI Terraformコードの生成（Claude Codeの生成能力）
- `generated/{project-name}/terraform/` に出力

### C-3: deploy-infra.md
- `oci_rm.py` の `create_stack()` 呼び出し
- `run_plan()` → 結果確認
- `run_apply()` → `wait_for_job()` でステータス監視
- `get_stack_outputs()` で出力取得

### C-4: generate-app.md
- `hearing/result.json` の読み込み
- アプリケーションコード生成（Claude Codeの生成能力）
- テストコード生成 → テスト実行
- `generated/{project-name}/app/` に出力

### C-5: deploy-app.md
- `deployer.py` の各関数呼び出し
- インフラ情報（Stack outputs）に基づきデプロイ先を決定
- `build_image()` → `push_to_ocir()` → `deploy_to_*()` → `wait_for_deployment()`

### C-6: verify.md
- `e2e_runner.py` の `health_check()` → `run_test_suite()` → `generate_report()`
- テスト失敗時の診断情報収集

### C-7: build-demo-env.md (Workflow)
- hearing.md → generate-terraform.md → (deploy-infra.md || generate-app.md) → deploy-app.md → verify.md
- 並行実行: deploy-infra と generate-app を同時実行
- `reporter.py` で全体進捗レポート
