# Iteration 2: Deploy-Infra, Deploy-App, Verify Skills + Workflow Evaluation

**Scenario**: ticket-system-demo, compute_type=container_instances, MySQL, LB, Node.js/Express, authentication
**Date**: 2026-03-17
**Evaluation Type**: Structural (no OCI execution)
**Comparison Baseline**: Iteration 1 (inventory-api, compute, ATP, Python/FastAPI)

---

## 0. Score Comparison: Iteration 1 vs Iteration 2

### deploy-infra

| Dimension | Iter1 | Iter2 | Delta |
|-----------|-------|-------|-------|
| Clarity | 4/5 | 4/5 | +0 |
| Completeness | 4/5 | 4/5 | +0 |
| Correctness | 3/5 | 3/5 | +0 |

**Commentary**: deploy-infra was unchanged between iterations. The same issues from Iter1 persist (terraform.tfvars PLACEHOLDERs, sensitive outputs). No regressions, no improvements.

### deploy-app

| Dimension | Iter1 | Iter2 | Delta |
|-----------|-------|-------|-------|
| Clarity | 3/5 | 4/5 | **+1** |
| Completeness | 2/5 | 3/5 | **+1** |
| Correctness | 2/5 | 3/5 | **+1** |

**Commentary**: Significant improvements. Phase 3.5 is now DB-type-aware, OCIR auth added, Compute path has concrete SSH instructions, Phase 6 is language-aware. However, the Container Instances env_vars API gap persists and new issues were introduced.

### verify

| Dimension | Iter1 | Iter2 | Delta |
|-----------|-------|-------|-------|
| Clarity | 4/5 | 4/5 | +0 |
| Completeness | 3/5 | 4/5 | **+1** |
| Correctness | 4/5 | 4/5 | +0 |

**Commentary**: Test spec generation is now systematic (read routes, build specs). Authenticated endpoint handling is documented with session workaround and result merging code. Negative test cases now mentioned.

### workflow (build-demo-env)

| Dimension | Iter1 | Iter2 | Delta |
|-----------|-------|-------|-------|
| Clarity | 4/5 | 5/5 | **+1** |
| Completeness | 3/5 | 4/5 | **+1** |
| Correctness | 3/5 | 4/5 | **+1** |

**Commentary**: Error gates added to every step. Data flow documented explicitly. Simplified to sequential execution (no more ambiguous parallel). Cleanup guidance added on infra failure steps.

---

## 1. Iter1 Issue Resolution Status

### Critical Issues

| Iter1 ID | Description | Fixed? | Notes |
|----------|-------------|--------|-------|
| DI-01 | terraform.tfvars lacks PLACEHOLDERs for all required vars | **NO** | deploy-infra unchanged; this is a generate-terraform responsibility |
| DI-02 | Stack outputs don't contain db_host/port expected by deploy-app | **PARTIALLY** | Phase 3.5 now DB-type-aware; MySQL path reads correct keys, but depends on Terraform actually outputting them |
| DI-03 | terraform.tfvars file not actually generated | **NO** | generate-terraform scope, not addressed here |
| DA-01 | Phase 3.5 assumes MySQL, not ATP; hardcodes NODE_ENV | **YES** | Phase 3.5 rewritten with ATP/MySQL/no-DB branches; NODE_ENV replaced with APP_ENV |
| DA-02 | Compute deploy path lacks concrete SSH instructions | **YES** | Full SSH commands with opc user, docker login, docker pull, docker run, env_flags |

### High Issues

| Iter1 ID | Description | Fixed? | Notes |
|----------|-------------|--------|-------|
| DA-03 | `deploy_to_container_instances` API missing env_vars | **NO** | deployer.py unchanged; skill comment says "environment_variables引数で渡す" but API still lacks the parameter |
| DA-04 | `deploy_to_functions` ignores function_name | **NO** | deployer.py unchanged |
| DA-05 | OKE kubeconfig extraction not shown | **YES** | Now shows base64 decode + file write |
| DA-06 | Phase 6 DB init uses `npm run seed` for all languages | **YES** | Language-aware table: Python -> `python -m seed`, Node.js -> `npm run seed` |
| DA-09 | OCIR push requires authentication | **YES** | Phase 2.5 added with docker login instructions and auth token prompt |
| VE-01 | Test spec generation too vague | **YES** | Systematic: read routes from app, build specs per endpoint, include error cases |
| VE-02 | run_test_suite does not support session | **YES** | Explicit workaround documented: session.get() individually, merge results |
| WF-01 | Parallel execution unclear | **YES** | Simplified to sequential |
| WF-03 | No error gates between steps | **YES** | Error gate added after every step with cleanup guidance |

### Medium Issues

| Iter1 ID | Description | Fixed? | Notes |
|----------|-------------|--------|-------|
| DI-04 | create_stack upsert unclear | **NO** | deploy-infra unchanged, but existing comment already says "既存Stack検出時は自動更新" |
| DI-05 | Sensitive outputs lost in log-parsing fallback | **NO** | deploy-infra unchanged |
| DA-07 | wait_for_deployment returns immediately for compute | **NO** | deployer.py unchanged |
| DA-08 | endpoints.json missing stack_id | **NO** | deployer.py unchanged |
| DA-10 | Functions invoke endpoint unresolved | **NO** | deploy-app unchanged for Functions path |
| VE-03 | No POST payload generation guidance | **YES** | Now says to reference app's schema/model definitions |
| VE-04 | No negative test cases | **YES** | Now includes 404, 422 guidance per resource |
| WF-02 | _stack_id prefix convention undocumented | **NO** | Still undocumented but harmless |
| WF-04 | No cleanup/rollback | **PARTIALLY** | Error gates mention cleanup via OCI Console/Destroy for infra steps |
| WF-05 | Data flow not documented | **YES** | Data flow diagram added at top of workflow |

### Low Issues

| Iter1 ID | Description | Fixed? | Notes |
|----------|-------------|--------|-------|
| DI-06 | AUTO_APPROVED behavior undocumented | **NO** | Unchanged |
| VE-05 | Dual .md/.json output | **NO** | Unchanged, acceptable |
| VE-06 | Health check not merged into test suite | **NO** | Unchanged, acceptable as gate |

---

## 2. Detailed Evaluation per Skill (Iteration 2)

### 2.1 deploy-infra

**No changes from Iter1.** All previous findings persist. For the MySQL scenario, the key question is whether Terraform outputs include `db_host`, `db_port`, `db_user`, `db_password` that deploy-app Phase 3.5 now expects. This depends entirely on what generate-terraform produces for a MySQL configuration -- deploy-infra is a pass-through.

### 2.2 deploy-app

#### Phase 3.5 env_vars: DB-type-aware (Question 1)

**Assessment: YES, rewritten and improved.**

The Phase 3.5 code now branches on `db_type`:
- **ATP**: Uses `db_connection_string` from stack_outputs directly (TNS format). Correct.
- **MySQL**: Reads `db_host`, `db_port`, `db_user`, `db_password` individually and constructs `mysql://` connection string. Correct for MySQL.
- **No DB**: Minimal env_vars with PORT and APP_ENV. Correct.

**Remaining concern**: The MySQL path reads `db_password` from stack_outputs, but Terraform `random_password` outputs are typically `sensitive = true` and may not appear in outputs. The skill adds a fallback note: "stack_outputsにパスワードが含まれない場合, terraform.tfvarsからdb_admin_passwordを読み取る". This is a reasonable workaround.

**For the test scenario (MySQL)**: The Phase 3.5 MySQL branch should work correctly IF the Terraform outputs include `db_host` and `db_port`. This is a generate-terraform responsibility.

#### Phase 2.5: OCIR Authentication (Question 2)

**Assessment: YES, added.**

New Phase 2.5 provides:
- `login_to_ocir` function call (or manual docker login)
- Full `docker login` command template with region, namespace, user email, auth token
- Instruction to prompt user for auth token if not available

**Issue**: `login_to_ocir` is referenced but does not exist in `deployer.py`. The manual fallback covers this, but the primary code path will raise ImportError.

#### Container Instances deploy path (Question 3)

**Assessment: STILL BROKEN.**

The skill says "env_varsはcontainer_instance作成時にenvironment_variables引数で渡す" but `deploy_to_container_instances()` in deployer.py still has signature:
```python
def deploy_to_container_instances(compartment_id, image_url, display_name, subnet_id, shape, ocpus, memory_gb)
```
No `environment_variables` or `env_vars` parameter. The function's internal JSON spec only includes `displayName` and `imageUrl` for the container -- no environment variables.

**This is a blocking issue for the test scenario** (container_instances is the compute_type).

#### Phase 6 language-awareness (Question 4)

**Assessment: YES, improved.**

Phase 6 now includes a language-to-seed-command table:
| Language | Seed Command |
|----------|-------------|
| Python | `python -m seed` or `python seed.py` |
| Node.js | `npm run seed` |

For the test scenario (Node.js), `npm run seed` will be used. Correct.

### 2.3 verify

#### Systematic test spec generation (Question 5)

**Assessment: YES, improved.**

Phase 3 now has a 4-step process:
1. Read `custom_requirements` from hearing/result.json to infer endpoints
2. Read routing definitions from `generated/{project_name}/app/`
3. Generate GET/POST/PUT specs per endpoint, with schema-derived payloads
4. Include error cases (404, 422) per resource

This is a significant improvement over "アプリの機能に応じて追加".

#### Authenticated endpoint handling (Question 6)

**Assessment: YES, improved.**

The verify skill now provides:
1. Login request to `/auth/login` with sample credentials from seed data
2. Session-based testing for authenticated endpoints
3. Explicit warning that `run_test_suite` doesn't support sessions
4. Complete result merging code (extends results list, updates total/passed/failed counts)

**For the test scenario (authentication required)**: The approach is sound. The agent will:
1. POST to `/auth/login` with `admin`/`password123`
2. Use the session for dashboard/tasks endpoints
3. Merge results into the main test suite

**Remaining concern**: The login credentials (`admin`/`password123`) are hardcoded. They should match whatever generate-app's seed data creates. If seed data uses different credentials, all auth tests fail.

### 2.4 workflow (build-demo-env)

#### Error gates (Question 7)

**Assessment: YES, added.**

Every step now has: "エラーゲート: このステップが失敗した場合、以降のステップは実行せず、エラー内容をユーザーに報告してください。"

Steps 4-6 add cleanup guidance: "部分的に作成されたリソースがある場合は、クリーンアップ方法を案内してください（OCI Console > Resource Manager > Stacks > Destroy）。"

#### Data flow documentation (Question 8)

**Assessment: YES, added.**

The workflow now has an explicit data flow section:
```
hearing → hearing/result.json
generate-terraform → generated/{project_name}/terraform/
deploy-infra → generated/{project_name}/stack_outputs.json
generate-app → generated/{project_name}/app/
deploy-app → generated/{project_name}/endpoints.json
verify → generated/{project_name}/test_results.json
```

#### Sequential simplification (Question 9)

**Assessment: YES, simplified.**

Steps 2 and 3 (generate-terraform, generate-app) are now separate sequential steps instead of the ambiguous parallel/fallback design. Step 3 (generate-app) runs before Step 4 (deploy-infra), which is correct -- app code must exist before deploy-app, and infra must exist before deploy-app. The ordering is: hearing -> generate-terraform -> generate-app -> deploy-infra -> deploy-app -> verify.

---

## 3. NEW Issues Introduced in Iteration 2

### ISSUE-DA-NEW-01: `login_to_ocir` function does not exist in deployer.py (High)
- **Severity**: High
- **Description**: Phase 2.5 references `from src.deployer import login_to_ocir` but this function does not exist in deployer.py. The manual fallback (docker login command) covers the use case, but the primary Python code path will fail with ImportError.
- **Impact**: Agent will encounter ImportError, then must fall back to manual docker login. Wastes a retry cycle.
- **Recommendation**: Either add `login_to_ocir()` to deployer.py or remove the Python import and only show the bash command.

### ISSUE-DA-NEW-02: Container Instances path references `result['public_ip']` but API may not return it (Medium)
- **Severity**: Medium
- **Description**: The CI deploy path does `endpoint_url = f"http://{result['public_ip']}:8080"` where `result` is the return value of `deploy_to_container_instances()`. However, the function returns `result.get("data", {})` from the OCI API. The Container Instance create response includes `vnics` with IP info, but the public IP may not be directly at `result['public_ip']` -- it's typically nested under `vnics[0].privateIp` and the public IP requires a separate VNIC attachment lookup, or the CI needs to be in a public subnet with public IP assignment enabled.
- **Impact**: `result['public_ip']` may be a KeyError. For the test scenario with LB, the endpoint should be the LB IP, not the CI IP.
- **Recommendation**: For scenarios with a Load Balancer, use `stack_outputs["lb_public_ip"]` as the endpoint instead of the CI's direct IP.

### ISSUE-DA-NEW-03: Load Balancer endpoint not considered (High - scenario-specific)
- **Severity**: High
- **Description**: The test scenario includes a Load Balancer. When LB is present, the application endpoint should be the LB's public IP, not the Container Instance's direct IP. The deploy-app skill's Container Instances path uses `result['public_ip']` from the CI, ignoring the LB entirely. The correct endpoint for a CI+LB setup is `http://{lb_public_ip}:80` or `https://{lb_public_ip}:443`.
- **Impact**: endpoints.json will have the wrong URL. All verify tests will fail.
- **Recommendation**: Add LB-aware endpoint resolution: if `stack_outputs` contains `lb_public_ip`, use that as the endpoint URL instead of the compute resource's direct IP.

### ISSUE-DA-NEW-04: `APP_ENV` vs framework-specific env var (Low)
- **Severity**: Low
- **Description**: Phase 3.5 now uses `APP_ENV: "production"` instead of `NODE_ENV`. For Node.js/Express, the standard env var is `NODE_ENV=production` which affects Express behavior (error handling, view caching, etc.). Using `APP_ENV` means Express won't run in production mode unless the app explicitly reads `APP_ENV`.
- **Impact**: Express app may run in development mode (verbose error pages, no caching) despite being deployed.
- **Recommendation**: For Node.js, include BOTH `NODE_ENV: "production"` and `APP_ENV: "production"`. The generic `APP_ENV` is fine as an additional variable but `NODE_ENV` is required for Express.

### ISSUE-VE-NEW-01: Hardcoded auth credentials assume specific seed data (Medium)
- **Severity**: Medium
- **Description**: Verify Phase 3 uses `username: "admin", password: "password123"` for login. These must match the seed data generated by generate-app. If generate-app creates different credentials, all authenticated tests fail silently (login returns 401, subsequent tests fail).
- **Impact**: Authentication tests may fail if credentials don't match.
- **Recommendation**: Read credentials from a well-known location (e.g., `generated/{project_name}/app/seed-credentials.json`) or document that generate-app must use these exact credentials.

---

## 4. Full Data Flow Trace (ticket-system-demo scenario)

```
hearing/result.json
  |-- project_name: "ticket-system-demo"     (used by ALL skills)
  |-- compute_type: "container_instances"     (used by deploy-app, verify)
  |-- database.type: "mysql"                  (used by deploy-app Phase 3.5)
  |-- language: "nodejs"                      (used by deploy-app Phase 6)
  |-- custom_requirements: [auth, tickets...] (used by verify Phase 3)
  |
  v
generated/ticket-system-demo/terraform/
  |-- *.tf files                              (used by deploy-infra)
  |-- terraform.tfvars [MAY BE MISSING]       (expected by deploy-infra Phase 1)
  |
  v
generated/ticket-system-demo/stack_outputs.json
  |-- db_host                                 (expected by deploy-app MySQL path)
  |-- db_port                                 (expected, default "3306")
  |-- db_user                                 (expected, default "admin")
  |-- db_password [SENSITIVE]                 (expected, fallback to tfvars)
  |-- public_subnet_id                        (used by deploy-app CI path)
  |-- lb_public_ip [EXPECTED BUT NOT USED]    ** NEW GAP: deploy-app ignores LB **
  |-- _stack_id                               (used by workflow Step 7)
  |
  v
generated/ticket-system-demo/app/
  |-- Dockerfile                              (used by deploy-app Phase 2)
  |-- routes/, models/, seed.js               (Node.js app code)
  |
  v
generated/ticket-system-demo/endpoints.json
  |-- url: "http://{CI_IP}:8080"              ** WRONG: should be LB IP **
  |-- health_url: "http://{CI_IP}:8080/health"
  |-- compute_type: "container_instances"
  |-- project_name: "ticket-system-demo"
  |
  v
generated/ticket-system-demo/test_results.json
  |-- total, passed, failed, results          (used by workflow Step 7)
```

### Data Contract Gaps (Iteration 2)

| Gap | Source | Consumer | Severity | Status vs Iter1 |
|-----|--------|----------|----------|-----------------|
| terraform.tfvars may not exist | generate-terraform | deploy-infra | Critical | **UNCHANGED** |
| `deploy_to_container_instances` has no env_vars param | deployer.py | deploy-app | Critical | **UNCHANGED** |
| LB endpoint not used when LB exists | stack_outputs | deploy-app | High | **NEW** |
| `login_to_ocir` function missing | deployer.py | deploy-app | High | **NEW** |
| CI `public_ip` may not be at top level of API response | OCI API | deploy-app | Medium | **NEW** |
| Auth credentials hardcoded in verify | verify | generate-app seed | Medium | **NEW** |
| `NODE_ENV` not set for Express apps | deploy-app | Express runtime | Low | **NEW** |

---

## 5. Python API Alignment (Changes from Iter1)

### deployer.py (UNCHANGED)

| Function | Skill References It? | API Has It? | Match? |
|----------|---------------------|-------------|--------|
| `login_to_ocir()` | **YES (Phase 2.5)** | **NO** | **MISMATCH** |
| `deploy_to_container_instances(..., env_vars)` | **YES (comment)** | **NO** | **MISMATCH** |

All other function signatures remain correctly aligned as documented in Iter1.

### e2e_runner.py (UNCHANGED)

All functions correctly aligned. No session support in `run_test_suite` -- workaround documented in skill.

---

## 6. Remaining Issues Summary (All Severities)

### Critical

| ID | Skill | Description | Origin |
|----|-------|-------------|--------|
| DI-01 | deploy-infra | terraform.tfvars PLACEHOLDERs for all required vars | Iter1 |
| DA-03 | deploy-app | `deploy_to_container_instances` API missing env_vars | Iter1 |

### High

| ID | Skill | Description | Origin |
|----|-------|-------------|--------|
| DA-NEW-01 | deploy-app | `login_to_ocir` function does not exist in deployer.py | **NEW** |
| DA-NEW-03 | deploy-app | LB endpoint not considered in CI+LB scenario | **NEW** |
| DA-04 | deploy-app | `deploy_to_functions` ignores function_name | Iter1 |
| DA-10 | deploy-app | Functions invoke endpoint unresolved | Iter1 |

### Medium

| ID | Skill | Description | Origin |
|----|-------|-------------|--------|
| DA-NEW-02 | deploy-app | CI `result['public_ip']` may not exist at expected path | **NEW** |
| DA-07 | deploy-app | wait_for_deployment returns immediately for compute | Iter1 |
| DI-05 | deploy-infra | Sensitive outputs lost in log-parsing fallback | Iter1 |
| VE-NEW-01 | verify | Hardcoded auth credentials | **NEW** |

### Low

| ID | Skill | Description | Origin |
|----|-------|-------------|--------|
| DA-NEW-04 | deploy-app | NODE_ENV not set for Express apps | **NEW** |
| DI-06 | deploy-infra | AUTO_APPROVED behavior undocumented | Iter1 |
| VE-05 | verify | Dual .md/.json output | Iter1 |

---

## 7. Scenario-Specific Execution Assessment

For the **ticket-system-demo** scenario (Container Instances + MySQL + LB + Node.js + Auth):

| Phase | Will It Work? | Blocking Issue |
|-------|--------------|----------------|
| deploy-infra: Stack create/plan/apply | Likely YES (if tfvars exists) | DI-01 (tfvars) |
| deploy-infra: Outputs extraction | YES | - |
| deploy-app: Docker build | YES | - |
| deploy-app: OCIR auth (Phase 2.5) | PARTIAL (ImportError then manual fallback) | DA-NEW-01 |
| deploy-app: OCIR push | YES (after manual auth) | - |
| deploy-app: env_vars (Phase 3.5) | YES (MySQL branch correct) | - |
| deploy-app: CI deploy (Phase 4) | **NO** - env_vars not passed to container | DA-03 |
| deploy-app: Endpoint resolution | **WRONG** - uses CI IP, not LB IP | DA-NEW-03 |
| deploy-app: DB init (Phase 6) | YES (`npm run seed` for Node.js) | - |
| verify: Health check | FAIL (wrong URL if LB) | DA-NEW-03 |
| verify: Auth test | MAYBE (depends on seed data match) | VE-NEW-01 |
| verify: Functional tests | FAIL (wrong URL) | DA-NEW-03 |

**Overall verdict**: The pipeline will **fail** at the Container Instances deployment step because environment variables cannot be passed to the container (DA-03), and even if that were fixed manually, the endpoint URL would be wrong because the Load Balancer IP is not used (DA-NEW-03).

---

## 8. Priority Improvements for Iteration 3

### P0 - Blocking

1. **Add `env_vars` parameter to `deploy_to_container_instances()` in deployer.py**
   - Add `environment_variables: dict | None = None` parameter
   - Include in container JSON spec: `"environmentVariables": environment_variables`
   - This has been identified in BOTH iterations and remains unfixed

2. **Add LB-aware endpoint resolution to deploy-app**
   - If `stack_outputs` contains `lb_public_ip`, use it as endpoint URL
   - Fall back to compute resource IP only when no LB exists
   - Affects all compute_types that can be fronted by an LB

3. **Add `login_to_ocir()` function to deployer.py**
   - Or remove the import from deploy-app Phase 2.5 and only use the bash command
   - The function should handle `docker login {region}.ocir.io -u {namespace}/{user} -p {token}`

### P1 - Important

4. **Ensure terraform.tfvars generation** in generate-terraform skill with all required PLACEHOLDERs
5. **Add `NODE_ENV=production`** to env_vars for Node.js apps (in addition to APP_ENV)
6. **Externalize seed credentials** -- generate-app should write a credentials file that verify can read
7. **Fix CI public_ip resolution** -- extract from VNIC info or use the CI get API response correctly

### P2 - Improvement

8. Add `session` support to `check_endpoint()` / `run_test_suite()` in e2e_runner.py
9. Add health check polling to `wait_for_deployment()` for compute type
10. Fix `deploy_to_functions` to use `function_name` parameter or remove it
11. Add Functions invoke endpoint resolution logic
12. Document sensitive output handling in deploy-infra

---

## 9. Overall Assessment

**Progress from Iteration 1**: Meaningful improvements across deploy-app, verify, and workflow. The Iter1 evaluation identified 26 issues total; 12 were fully fixed, 2 partially fixed, 12 remain. However, 5 new issues were introduced, bringing the total remaining to 17 (down from 26, but with new problem types).

**Key positive changes**:
- Phase 3.5 DB-type-awareness is well-implemented
- OCIR auth step added (Phase 2.5)
- Compute SSH instructions are now concrete
- Verify has systematic test generation and auth handling
- Workflow has error gates and data flow documentation
- Sequential simplification eliminates the parallel execution ambiguity

**Key remaining systemic issue**: The `deployer.py` module was NOT updated alongside the skill changes. This creates a growing gap between what the skills instruct and what the Python API supports. Specifically:
- `login_to_ocir()` referenced but doesn't exist
- `deploy_to_container_instances()` still lacks `env_vars`
- `wait_for_deployment()` still returns immediately for compute

**New systemic issue**: The Load Balancer endpoint gap (DA-NEW-03) is significant because many production scenarios use LBs. The deploy-app skill only considers the compute resource's direct IP, never checking for an LB frontend.

**The most impactful single fix for Iteration 3**: Update `deployer.py` to match the skills. The skills have evolved but the Python implementation has not kept pace. Adding `env_vars` to `deploy_to_container_instances()` and `login_to_ocir()` would unblock the container_instances path entirely.
