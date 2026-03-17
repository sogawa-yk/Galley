# Iteration 1: Deploy-Infra, Deploy-App, Verify Skills + Workflow Evaluation

**Scenario**: inventory-api, compute_type=compute, ATP, public access, Python/FastAPI
**Date**: 2026-03-17
**Evaluation Type**: Structural (no OCI execution)

---

## 1. deploy-infra Skill Evaluation

### Ratings
| Dimension | Score |
|-----------|-------|
| Clarity | 4/5 |
| Completeness | 4/5 |
| Correctness | 3/5 |

### Issues Found

#### ISSUE-DI-01: `terraform.tfvars` lacks PLACEHOLDER for all required variables (Critical)
- **Severity**: Critical
- **Description**: Phase 1 step 6 says to update `compartment_id = "PLACEHOLDER"` and `region = "PLACEHOLDER"` in terraform.tfvars. However, the generated `variables.tf` also has `compute_image_id` (no default, required), `region_key`, and `tenancy_namespace` that need values. The skill only addresses compartment_id and region, ignoring other required variables. The generate-terraform skill should output a tfvars with PLACEHOLDERs for ALL required variables, and deploy-infra should resolve ALL of them.
- **Impact**: Terraform plan will fail with "No value for required variable" errors for `compute_image_id`, `region_key`, `tenancy_namespace`.
- **Recommendation**: (1) generate-terraform should emit PLACEHOLDERs for all required variables. (2) deploy-infra Phase 1 should resolve all PLACEHOLDERs, including image OCID lookup, region key derivation, and namespace retrieval.

#### ISSUE-DI-02: `get_stack_outputs` return keys may not match deploy-app expectations (Critical)
- **Severity**: Critical
- **Description**: The `get_stack_outputs()` function in `oci_rm.py` extracts outputs from Terraform state. The Terraform outputs use snake_case names (`compute_public_ip`, `db_connection_string`, etc.). The `save_stack_outputs()` adds `_stack_id`, `_apply_job_id`, `_project_name` metadata. However, the deploy-app skill (Phase 3.5) expects `db_host`, `db_port`, `db_user`, `db_password` keys in stack_outputs -- **none of these are Terraform outputs**. The actual Terraform output is `db_connection_string` (a full Oracle connection string, not MySQL-style host:port). For ATP, the connection string format is `(description=(retry_count=...)(...))` -- not `mysql://user:pass@host:port/db`.
- **Impact**: deploy-app Phase 3.5 will find no `db_host`, `db_port`, etc. in stack_outputs. The entire env_vars construction is based on MySQL-style connection semantics, which does not apply to ATP.
- **Recommendation**: (1) deploy-app Phase 3.5 needs ATP-specific connection handling (use wallet-based connection or the TNS connection string directly). (2) Add `DB_CONNECTION_STRING` as a Terraform output and pass it through directly. (3) Remove the MySQL-specific host/port/user/password decomposition for ATP.

#### ISSUE-DI-03: No `terraform.tfvars` file was actually generated (High)
- **Severity**: High
- **Description**: Looking at the generated terraform files (`generated/inventory-api/terraform/`), there is no `terraform.tfvars` file. The generate-terraform evaluation noted the file was "Generated" but it is absent from the filesystem (Glob found only .tf files, no .tfvars). The `zip_terraform_dir()` function DOES include `.tfvars` files in the zip, but if none exist, the PLACEHOLDERs cannot be updated.
- **Impact**: Phase 1 step 6 ("update terraform.tfvars PLACEHOLDER values") will fail -- no file to update.
- **Recommendation**: Ensure generate-terraform actually creates `terraform.tfvars` with all required variable values or PLACEHOLDERs.

#### ISSUE-DI-04: Self-correction loop re-creates stack on every retry (Medium)
- **Severity**: Medium
- **Description**: In the Plan/Apply failure self-correction loops (2.3 and 2.5), the skill instructs to call `create_stack()` again after modifying Terraform code. The `create_stack()` function detects existing stacks by name and updates them. This is correct behavior and the comment says "既存Stack検出時は自動更新." However, the skill could be clearer that `create_stack` is being used as an "upsert" operation. An agent unfamiliar with the implementation might think a new stack is created each time.
- **Impact**: Low runtime impact (works correctly), but unclear instructions.
- **Recommendation**: Rename or clarify: "Update the stack with modified code (create_stack handles upsert)."

#### ISSUE-DI-05: No handling of `db_connection_string` sensitive output (Medium)
- **Severity**: Medium
- **Description**: The Terraform output `db_connection_string` is marked `sensitive = true`. The `get_stack_outputs()` function reads from tfstate where sensitive values ARE present. However, if the fallback log-parsing strategy is used, sensitive outputs are redacted in logs. The skill does not mention this distinction.
- **Impact**: If tfstate strategy fails and logs are used as fallback, `db_connection_string` will be missing from stack_outputs.
- **Recommendation**: Add a note that sensitive outputs require the tfstate strategy and cannot be recovered from logs.

#### ISSUE-DI-06: `run_apply` uses AUTO_APPROVED without prior plan_job_id reference (Low)
- **Severity**: Low
- **Description**: `run_apply()` uses `--apply-job-plan-resolution AUTO_APPROVED`, which means it does not reference a specific plan job. This is acceptable for demo environments but means the most recent plan is auto-approved. The skill does not explain this behavior.
- **Impact**: Minor -- the behavior is correct for the use case but could surprise users.

---

## 2. deploy-app Skill Evaluation

### Ratings
| Dimension | Score |
|-----------|-------|
| Clarity | 3/5 |
| Completeness | 2/5 |
| Correctness | 2/5 |

### Issues Found

#### ISSUE-DA-01: Phase 3.5 env_vars construction assumes MySQL-style DB, not ATP (Critical)
- **Severity**: Critical
- **Description**: Phase 3.5 constructs env_vars with `db_host`, `db_port`, `db_user`, `db_password`, `db_name`, and builds a `DB_CONNECTION_STRING` as `mysql://...`. For the test scenario (ATP), the actual connection mechanism is:
  - ATP uses Oracle wallet-based connections or TNS connection strings
  - The Terraform output is `db_connection_string` which is an Oracle TNS descriptor, NOT a URL
  - There is no `db_host` or `db_port` output from Terraform
  - The admin password is generated by `random_password` in Terraform and marked sensitive
  - `NODE_ENV: "production"` is hardcoded but this is a Python/FastAPI app (not Node.js)
- **Impact**: The entire env_vars block is wrong for ATP databases. The application will fail to connect to the database.
- **Recommendation**: (1) Make Phase 3.5 database-type-aware (ATP vs MySQL vs PostgreSQL). (2) For ATP, pass `DB_CONNECTION_STRING` directly from Terraform output. (3) Replace `NODE_ENV` with a generic `APP_ENV` or make it framework-aware.

#### ISSUE-DA-02: Compute deploy path lacks concrete SSH instructions (Critical)
- **Severity**: Critical
- **Description**: The Compute deploy path says "SSH で接続し docker pull + docker run" with `env_vars` passed via `-e` options. But there are no actual instructions for:
  1. How to SSH (what key? what user? `opc` is standard for Oracle Linux but not mentioned)
  2. How to authenticate docker pull from OCIR (requires `docker login` with auth token)
  3. The actual docker run command to execute
  4. How to handle SSH key -- neither the hearing result nor Terraform outputs include an SSH key
  5. How to transfer the SSH private key to the agent environment
- **Impact**: An agent cannot execute this deploy path without significant unguided improvisation.
- **Recommendation**: Add a complete Compute deployment subsection with: SSH user (`opc`), OCIR docker login command, full `docker run` command template, and SSH key resolution strategy.

#### ISSUE-DA-03: `deploy_to_container_instances` API does not accept `environment_variables` (High)
- **Severity**: High
- **Description**: The skill comment says "env_varsはcontainer_instance作成時にenvironment_variables引数で渡す" but the actual `deploy_to_container_instances()` function signature is `(compartment_id, image_url, display_name, subnet_id, shape, ocpus, memory_gb)` -- there is NO `environment_variables` parameter. The function constructs the container spec internally with only `displayName` and `imageUrl`. Environment variables are not passed to the container.
- **Impact**: Container Instances deployments will have no environment variables. Database connectivity and app configuration will fail.
- **Recommendation**: Add `env_vars: dict | None = None` parameter to `deploy_to_container_instances()` and include them in the container JSON spec as `environmentVariables`.

#### ISSUE-DA-04: `deploy_to_functions` does not use `function_name` parameter (High)
- **Severity**: High
- **Description**: The `deploy_to_functions()` function accepts `function_name` but never uses it. The `fn deploy` command is executed with `--app function_app_id` but does not specify `--function function_name`. The function name comes from `func.yaml` in the app directory.
- **Impact**: The `function_name` parameter is misleading -- it has no effect. The actual function name depends on `func.yaml` content.
- **Recommendation**: Either use `function_name` in the fn deploy command or remove the parameter and document that the name comes from func.yaml.

#### ISSUE-DA-05: OKE deploy path lacks kubeconfig extraction from stack_outputs (High)
- **Severity**: High
- **Description**: The OKE path says "kubeconfig を stack_outputs から取得・ファイル保存" but the Terraform outputs for a compute scenario don't include kubeconfig. More importantly, even for an OKE scenario, the Terraform output would be `oke_kubeconfig` (base64-encoded), but the skill doesn't show how to decode and write it to a file. The code just says `deploy_to_oke(kubeconfig_path="kubeconfig.yaml", manifests_dir="k8s/")` without showing the preceding file creation.
- **Impact**: OKE deployments will fail because kubeconfig.yaml doesn't exist.
- **Recommendation**: Add explicit instructions to extract, decode, and write kubeconfig from stack_outputs before calling deploy_to_oke.

#### ISSUE-DA-06: Phase 6 DB initialization assumes Node.js (`npm run seed`) (High)
- **Severity**: High
- **Description**: Phase 6 DB initialization examples use `npm run seed` for all scenarios (OKE kubectl example, CI/Compute fallback). For this Python/FastAPI scenario, the seed command would be something like `python -m app.seed` or `python seed.py`, not `npm run seed`. The skill is not language-aware.
- **Impact**: DB initialization will fail for non-Node.js projects.
- **Recommendation**: Make seed command language-aware. Add mapping: Python -> `python -m seed` or `python seed.py`, Node.js -> `npm run seed`, etc. Or use a generic `APP_SEED_COMMAND` env var.

#### ISSUE-DA-07: `wait_for_deployment` for compute returns immediately (Medium)
- **Severity**: Medium
- **Description**: `wait_for_deployment()` for `deploy_type != "container_instances" and != "oke"` (which includes "compute") simply returns `{"status": "deployed"}` immediately. There is no actual health check or readiness verification for compute deployments. Docker containers on compute instances may not be ready yet.
- **Impact**: Phase 5 completes instantly for compute, but the app may not be ready. The subsequent endpoints.json will have a URL that may not respond yet.
- **Recommendation**: Add HTTP health check polling for compute deployments (similar to what e2e_runner.health_check does).

#### ISSUE-DA-08: `save_endpoints` output does not include `_stack_id` (Medium)
- **Severity**: Medium
- **Description**: The `save_endpoints()` function saves `url`, `health_url`, `compute_type`, `project_name`. The verify skill expects these keys (data contract confirmed). However, the workflow Step 7 reads `stack_outputs.get("_stack_id")` separately. This is fine, but if stack_outputs.json is unavailable at Step 7, the stack_id is lost. Consider adding it to endpoints.json for resilience.
- **Impact**: Low -- works as designed, but fragile if stack_outputs.json is corrupted/missing.

#### ISSUE-DA-09: OCIR push requires authentication not addressed (Medium)
- **Severity**: Medium
- **Description**: `push_to_ocir()` calls `docker push` directly but OCIR requires authentication first (`docker login {region}.ocir.io`). The skill does not mention OCIR authentication, auth token generation, or the docker login step.
- **Impact**: `docker push` will fail with authentication error.
- **Recommendation**: Add OCIR login instructions before push. Requires auth token (from OCI IAM) or instance principal token.

#### ISSUE-DA-10: Functions deploy path missing invoke endpoint resolution (Medium)
- **Severity**: Medium
- **Description**: For Functions, `endpoint_url = stack_outputs.get("functions_invoke_endpoint", "")`. This key must be a Terraform output. But the current outputs.tf (compute scenario) doesn't have it. Even for a Functions scenario, the invoke endpoint format is `https://{function_invoke_endpoint}/20181201/functions/{function_id}/actions/invoke` which requires additional API calls to resolve.
- **Impact**: Functions endpoint URL will be empty string.
- **Recommendation**: Add Functions invoke endpoint construction logic or a helper function.

---

## 3. verify Skill Evaluation

### Ratings
| Dimension | Score |
|-----------|-------|
| Clarity | 4/5 |
| Completeness | 3/5 |
| Correctness | 4/5 |

### Issues Found

#### ISSUE-VE-01: Test spec generation is too vague -- "アプリの機能に応じて追加" (High)
- **Severity**: High
- **Description**: Phase 3 shows a template with only the health check test spec, then says "アプリの機能に応じて追加" with commented-out examples. For the inventory-api scenario, the agent must infer ALL API endpoints from `hearing/result.json` and generate test specs for each. The skill provides no systematic method to enumerate endpoints from the hearing result.
- **Impact**: Test coverage depends entirely on agent judgment. Different agents will produce vastly different test suites.
- **Recommendation**: Add a systematic approach: (1) Read the generated app's route definitions, (2) Generate GET tests for all list endpoints, (3) Generate POST tests with sample payloads for create endpoints, (4) For CRUD resources, test the full lifecycle (POST -> GET -> PUT -> DELETE).

#### ISSUE-VE-02: `run_test_suite` does not support `session` parameter (High)
- **Severity**: High
- **Description**: Phase 3 notes that authenticated endpoints need a `requests.Session` object, and the test_specs include a `session` key. But `run_test_suite()` internally calls `check_endpoint()` which uses `requests.request()` -- it does NOT accept or use a session object. The skill correctly warns about this ("run_test_suite はセッションオブジェクトをサポートしていない場合、個別に session.get() でテスト") but this means the entire authenticated testing path bypasses the test framework.
- **Impact**: Authenticated test results are collected outside `run_test_suite` and must be manually merged into the results dict for reporting.
- **Recommendation**: Either (1) add session support to `check_endpoint`/`run_test_suite`, or (2) provide explicit code for merging manual test results into the results dict.

#### ISSUE-VE-03: No POST test payload generation guidance (Medium)
- **Severity**: Medium
- **Description**: The test spec example shows `"payload": {...}` for POST tests but provides no guidance on generating valid payloads. For inventory-api, a POST to `/api/items` needs a valid JSON body matching the Pydantic schema. The skill should reference the generated app's schemas.
- **Impact**: Agents may generate invalid payloads that fail schema validation, producing false test failures.
- **Recommendation**: Add guidance: "Read the generated app's schema definitions (models/schemas) to construct valid test payloads."

#### ISSUE-VE-04: No negative test cases (Medium)
- **Severity**: Medium
- **Description**: All test specs are positive cases (expected 200). No guidance on testing error cases (404 for nonexistent resource, 422 for invalid input, 401 for unauthenticated access).
- **Impact**: Test suite only validates happy path.
- **Recommendation**: Add: "Include at least one negative test per resource (e.g., GET nonexistent ID -> 404)."

#### ISSUE-VE-05: Report saved as both .md and .json but only .json used downstream (Low)
- **Severity**: Low
- **Description**: Phase 4 generates both `test_results.md` (via `generate_report`) and `test_results.json` (manual save). The workflow Step 7 reads only `test_results.json`. The `.md` report is for human consumption only.
- **Impact**: None functionally, but the dual output could be confusing.

#### ISSUE-VE-06: Health check result not merged into test suite results (Low)
- **Severity**: Low
- **Description**: Phase 2 runs `health_check()` which returns a separate result dict. Phase 3 runs `run_test_suite()` which includes a health check test spec. The Phase 2 health check result is never merged into the Phase 3 results. The final report only reflects Phase 3 results.
- **Impact**: Minor duplication. Phase 2 health check serves as a gate (fail fast) before Phase 3.

---

## 4. build-demo-env.md Workflow Evaluation

### Ratings
| Dimension | Score |
|-----------|-------|
| Clarity | 4/5 |
| Completeness | 3/5 |
| Correctness | 3/5 |

### Issues Found

#### ISSUE-WF-01: Step 3 parallel execution assumes agent background capability (High)
- **Severity**: High
- **Description**: Step 3 says to run deploy-infra as a "バックグラウンドエージェント" in parallel with generate-app. Claude Code does support background tasks via `run_in_background`, but the skill invocation mechanism (`Use skill: deploy-infra`) does not clearly map to background execution. The fallback sequential order (generate-app first, then deploy-infra) is documented, which is good.
- **Impact**: In practice, parallel execution is unlikely to work as described. The fallback is needed.
- **Recommendation**: Simplify to always sequential: generate-app -> deploy-infra. Or provide explicit `run_in_background` integration instructions.

#### ISSUE-WF-02: Step 7 `generate_summary` call uses `_stack_id` from stack_outputs (Medium)
- **Severity**: Medium
- **Description**: Step 7 reads `stack_outputs.get("_stack_id", "N/A")`. This key is set by `save_stack_outputs()` as a metadata field prefixed with `_`. The `generate_summary()` function expects `stack_id` as a plain string. This works correctly -- the `_stack_id` key in the JSON is accessed with the underscore prefix. The code is correct but the underscore prefix convention for metadata vs. Terraform outputs is not documented.
- **Impact**: No functional impact, but convention is undocumented.

#### ISSUE-WF-03: No error handling between steps (High)
- **Severity**: High
- **Description**: The workflow has no guidance on what happens if a step fails. If deploy-infra fails (after retries), should deploy-app still execute? If deploy-app fails, should verify still run? The workflow is purely sequential with no error branching.
- **Impact**: A failure in Step 3 will cascade into confusing errors in Steps 5-7.
- **Recommendation**: Add explicit error gates: "If deploy-infra fails, STOP and report. Do not proceed to deploy-app."

#### ISSUE-WF-04: No cleanup/rollback guidance (Medium)
- **Severity**: Medium
- **Description**: If the workflow fails partway through, partially created resources are left running (and costing money). The workflow mentions "Destroy" in the final report but has no automated cleanup on failure.
- **Impact**: Failed demo environments accumulate costs.
- **Recommendation**: Add a failure cleanup section: "On failure, offer to run destroy on the stack."

#### ISSUE-WF-05: Missing data dependency documentation (Low)
- **Severity**: Low
- **Description**: The workflow does not explicitly document the data flow between skills:
  - hearing -> `hearing/result.json`
  - generate-terraform -> `generated/{project_name}/terraform/`
  - deploy-infra -> `generated/{project_name}/stack_outputs.json`
  - generate-app -> `generated/{project_name}/app/`
  - deploy-app -> `generated/{project_name}/endpoints.json`
  - verify -> `generated/{project_name}/test_results.json`
  This is implicit from the skills but should be explicit in the workflow.

---

## 5. Inter-Skill Data Flow Analysis

### Full Data Flow Trace (inventory-api scenario)

```
hearing/result.json
  |-- project_name: "inventory-api"      (used by ALL skills)
  |-- compute_type: "compute"            (used by deploy-app, verify)
  |-- database.type: "atp"               (used by deploy-app Phase 3.5)
  |
  v
generated/inventory-api/terraform/
  |-- *.tf files                         (used by deploy-infra)
  |-- terraform.tfvars [MISSING!]        (expected by deploy-infra Phase 1)
  |
  v
generated/inventory-api/stack_outputs.json
  |-- compute_public_ip                  (used by deploy-app Compute path)
  |-- compute_instance_id                (used by deploy-app Compute path)
  |-- db_connection_string [SENSITIVE]   (should be used by deploy-app)
  |-- db_host [NOT PRESENT]             ** MISMATCH: deploy-app expects this **
  |-- db_port [NOT PRESENT]             ** MISMATCH: deploy-app expects this **
  |-- db_user [NOT PRESENT]             ** MISMATCH: deploy-app expects this **
  |-- db_password [NOT PRESENT]         ** MISMATCH: deploy-app expects this **
  |-- _stack_id                          (used by workflow Step 7)
  |
  v
generated/inventory-api/app/
  |-- Dockerfile                         (used by deploy-app Phase 2)
  |-- *.py, requirements.txt             (app code)
  |
  v
generated/inventory-api/endpoints.json
  |-- url                                (used by verify, workflow Step 7)
  |-- health_url                         (used by verify)
  |-- compute_type                       (informational)
  |-- project_name                       (informational)
  |
  v
generated/inventory-api/test_results.json
  |-- total, passed, failed, results     (used by workflow Step 7)
```

### Data Gaps Identified

| Gap | Source Skill | Consumer Skill | Severity |
|-----|-------------|----------------|----------|
| `terraform.tfvars` not generated | generate-terraform | deploy-infra | Critical |
| `db_host/port/user/password` not in stack_outputs | deploy-infra (Terraform) | deploy-app | Critical |
| ATP connection string is TNS format, not URL | deploy-infra (Terraform) | deploy-app | Critical |
| SSH key not in any artifact | generate-terraform | deploy-app (Compute) | Critical |
| OCIR auth token not addressed | (none) | deploy-app | High |
| `compute_image_id` not resolved | generate-terraform | deploy-infra | High |
| `region_key` not resolved | generate-terraform | deploy-infra | High |

---

## 6. Python API Alignment Analysis

### oci_rm.py vs deploy-infra skill

| Function | Skill Usage | Actual Signature | Match? |
|----------|------------|------------------|--------|
| `create_stack(compartment_id, terraform_dir, display_name)` | Correct | `create_stack(compartment_id, terraform_dir, display_name, terraform_version="1.5.x")` | Yes (optional param omitted, OK) |
| `run_plan(stack_id)` | Correct | `run_plan(stack_id) -> str` | Yes |
| `wait_for_job(job_id, timeout, interval)` | Correct | `wait_for_job(job_id, timeout=3600, interval=30) -> dict` | Yes |
| `get_job_logs(job_id)` | Correct | `get_job_logs(job_id) -> str` | Yes |
| `run_apply(stack_id)` | Correct | `run_apply(stack_id) -> str` | Yes |
| `get_stack_outputs(stack_id, apply_job_id)` | Correct | `get_stack_outputs(stack_id, job_id) -> dict` | Yes (param name differs: `apply_job_id` vs `job_id` -- minor) |
| `save_stack_outputs(outputs, stack_id, job_id, project_name, output_path)` | Correct | Matches | Yes |

### deployer.py vs deploy-app skill

| Function | Skill Usage | Actual Signature | Match? |
|----------|------------|------------------|--------|
| `build_image(app_dir, image_name)` | Correct | `build_image(app_dir, image_name, tag="latest") -> str` | Yes |
| `get_tenancy_namespace()` | Correct | `get_tenancy_namespace() -> str` | Yes |
| `push_to_ocir(image_name, region, tenancy_namespace, repo_name)` | Correct | `push_to_ocir(image_name, region, tenancy_namespace, repo_name, tag="latest") -> str` | Yes |
| `deploy_to_oke(kubeconfig_path, manifests_dir)` | Correct | `deploy_to_oke(kubeconfig_path, manifests_dir) -> dict` | Yes |
| `deploy_to_container_instances(compartment_id, image_url, display_name, subnet_id)` | **Mismatch** | No `env_vars` parameter | **No** |
| `deploy_to_functions(app_dir, function_app_id, function_name)` | Correct | Matches but `function_name` unused | Partial |
| `wait_for_deployment(deploy_type, resource_id)` | Correct | Matches | Yes |
| `save_endpoints(url, project_name, compute_type, output_path)` | Correct | Matches | Yes |

### e2e_runner.py vs verify skill

| Function | Skill Usage | Actual Signature | Match? |
|----------|------------|------------------|--------|
| `health_check(url, timeout, retries, interval)` | Correct | Matches | Yes |
| `run_test_suite(test_specs)` | Correct | `run_test_suite(test_specs: list[dict]) -> dict` | Yes |
| `generate_report(test_results, output_path)` | Correct | Matches | Yes |

### reporter.py vs workflow Step 7

| Function | Workflow Usage | Actual Signature | Match? |
|----------|--------------|------------------|--------|
| `generate_summary(project_name, stack_id, endpoints, test_results, output_path)` | Correct | Matches exactly | Yes |

---

## 7. Compute-Type Path Coverage Analysis

| Path | deploy-infra | deploy-app | verify |
|------|-------------|------------|--------|
| **OKE** | N/A (generic) | Has instructions but kubeconfig extraction missing | Generic (same for all) |
| **Container Instances** | N/A (generic) | Has instructions but env_vars not passed to API | Generic |
| **Compute** | N/A (generic) | Has skeleton but missing SSH/OCIR auth/docker commands | Generic |
| **Functions** | N/A (generic) | Has instructions but function_name unused, invoke URL unresolved | Generic |

**Assessment**: deploy-infra is compute-type-agnostic (correct -- Terraform handles all types). deploy-app has all four paths but each has significant gaps. verify is compute-type-agnostic (correct -- tests against HTTP endpoints).

---

## 8. Summary of All Issues by Severity

### Critical (Must Fix Before Execution)

| ID | Skill | Description |
|----|-------|-------------|
| DI-01 | deploy-infra | terraform.tfvars lacks PLACEHOLDERs for all required variables |
| DI-02 | deploy-infra/deploy-app | Stack outputs don't contain db_host/port/user/password expected by deploy-app |
| DA-01 | deploy-app | Phase 3.5 env_vars assumes MySQL, not ATP; hardcodes NODE_ENV for Python app |
| DA-02 | deploy-app | Compute deploy path has no concrete SSH/docker instructions |
| DI-03 | deploy-infra | terraform.tfvars file not actually generated by generate-terraform |

### High (Should Fix)

| ID | Skill | Description |
|----|-------|-------------|
| DA-03 | deploy-app | `deploy_to_container_instances` API missing env_vars parameter |
| DA-04 | deploy-app | `deploy_to_functions` ignores function_name parameter |
| DA-05 | deploy-app | OKE kubeconfig extraction from stack_outputs not shown |
| DA-06 | deploy-app | Phase 6 DB init uses `npm run seed` for all languages |
| DA-09 | deploy-app | OCIR push requires authentication not addressed |
| VE-01 | verify | Test spec generation is too vague, no systematic method |
| VE-02 | verify | run_test_suite does not support session for authenticated tests |
| WF-01 | workflow | Parallel execution mechanism unclear |
| WF-03 | workflow | No error handling/gates between steps |

### Medium

| ID | Skill | Description |
|----|-------|-------------|
| DI-04 | deploy-infra | Self-correction "create_stack" upsert behavior unclear in instructions |
| DI-05 | deploy-infra | Sensitive Terraform outputs may be lost in log-parsing fallback |
| DA-07 | deploy-app | wait_for_deployment returns immediately for compute |
| DA-08 | deploy-app | endpoints.json does not include stack_id (fragile) |
| DA-10 | deploy-app | Functions invoke endpoint resolution missing |
| VE-03 | verify | No POST test payload generation guidance |
| VE-04 | verify | No negative test cases |
| WF-02 | workflow | _stack_id metadata prefix convention undocumented |
| WF-04 | workflow | No cleanup/rollback on failure |

### Low

| ID | Skill | Description |
|----|-------|-------------|
| DI-06 | deploy-infra | AUTO_APPROVED apply behavior undocumented |
| VE-05 | verify | Dual .md/.json output, only .json used downstream |
| VE-06 | verify | Phase 2 health check result not merged into Phase 3 results |
| WF-05 | workflow | Data flow between skills not explicitly documented |

---

## 9. Top Priority Improvements

### P0 - Blocking (Cannot Execute Without Fix)

1. **Fix the data contract between Terraform outputs and deploy-app env_vars**. The current deploy-app Phase 3.5 is written for MySQL-style connections. Must be rewritten to handle each database type (ATP uses TNS/wallet, MySQL uses host:port, PostgreSQL uses host:port). Terraform outputs should include the fields that deploy-app actually needs.

2. **Generate terraform.tfvars** with all required variable values or PLACEHOLDERs from generate-terraform skill. deploy-infra Phase 1 must resolve ALL PLACEHOLDERs including `compute_image_id`, `region_key`, `tenancy_namespace`.

3. **Add concrete Compute deploy instructions** to deploy-app: SSH user, key resolution, OCIR docker login, full docker run command.

4. **Add OCIR authentication step** to deploy-app Phase 3 (before push_to_ocir).

### P1 - Important

5. Add `env_vars` parameter to `deploy_to_container_instances()` in deployer.py
6. Make deploy-app Phase 6 DB init language-aware (not just `npm run seed`)
7. Add error gates to workflow (stop on failure, don't cascade)
8. Improve verify skill Phase 3 with systematic endpoint enumeration
9. Add session support to e2e_runner or explicit manual test result merging code
10. Add OKE kubeconfig extraction/decode instructions

### P2 - Improvement

11. Add health check polling to `wait_for_deployment` for compute type
12. Add Functions invoke endpoint resolution logic
13. Add negative test cases to verify skill guidance
14. Add POST payload generation guidance referencing app schemas
15. Document data flow explicitly in workflow
16. Add cleanup/rollback guidance on failure

---

## 10. Overall Assessment

The deploy-infra skill is the strongest of the three, with clear phased instructions and good alignment with the Python API. Its main weakness is the assumption that terraform.tfvars will exist with the right PLACEHOLDERs.

The deploy-app skill is the weakest link in the chain. It has critical data contract mismatches (MySQL assumptions for ATP), incomplete deployment instructions for every compute type, and missing authentication steps. It reads as if it was designed for a Node.js/MySQL scenario and not generalized for the full matrix of languages and databases.

The verify skill is adequate but underspecified in test generation. It relies heavily on agent judgment to construct meaningful test suites.

The workflow orchestration is clean and readable but lacks error handling and explicit data flow documentation.

**The most critical systemic issue is the disconnect between Terraform outputs and deploy-app's expected inputs.** This is a cross-skill data contract violation that must be resolved before any execution attempt.
