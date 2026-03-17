# Iteration 3: Combined Evaluation Report (Hearing + Generate-Terraform)

**Scenario**: Python/Flask + OCI Functions (Serverless) + Object Storage + API Gateway, No DB, No LB
**Date**: 2026-03-17
**User Request**: 「画像リサイズAPIを作りたい。Python/Flaskでサーバーレス（OCI Functions）にデプロイ。Object Storageにアップロードされた画像を処理する。APIゲートウェイ経由でアクセス。技術検証用。」

---

## Part A: Hearing Skill Evaluation

### Phase 1: Request Analysis

**Clarity**: 5/5
**Completeness**: 4/5
**Correctness**: 5/5

**Extracted values using the enum mapping table**:

| Field | Extracted Value | Source Text | Mapping Entry Used |
|---|---|---|---|
| app_type | `"serverless"` | サーバーレス（OCI Functions） | app_type: サーバーレス -> `"serverless"` |
| language | `"python"` | Python/Flask | Direct |
| framework | `"flask"` | Python/Flask | Direct |
| compute_type | `"functions"` | サーバーレス（OCI Functions） | compute_type: Functions / サーバーレス -> `"functions"` |
| purpose | `"poc"` | 技術検証用 | purpose: 検証 / PoC / 技術検証 -> `"poc"` |
| additional_services | `["object_storage", "api_gateway"]` | Object Storage + APIゲートウェイ | additional_services mapping table |

**Key Test: "サーバーレス（OCI Functions）" -> compute_type="functions"**: PASS. The mapping table entry "Functions / サーバーレス -> functions" covers this directly. The parenthetical "(OCI Functions)" reinforces the mapping. No ambiguity.

**Improvement from Iter1/Iter2**: The mapping table (added after Iter1) continues to work well. This scenario tests a mapping path not exercised before -- the serverless/functions path.

**Remaining Issues**:

1. **MINOR: `app_type` mapping for serverless API**. The user says "画像リサイズAPI" which is technically an API, but also says "サーバーレス". The mapping table has both `app_type: API -> "api"` and `app_type: サーバーレス -> "serverless"`. Should app_type be `"api"` or `"serverless"`? The function-based nature suggests `"serverless"` is more appropriate, but an agent could reasonably choose `"api"`. The mapping table doesn't specify precedence when multiple app_type patterns match. **New issue not seen in Iter1/Iter2**.

---

### Phase 2: Question Generation

**Clarity**: 4/5
**Completeness**: 4/5
**Correctness**: 5/5

**Key Test: Container question auto-skip for Functions**: PASS. The skill explicitly states: "コンピュート種別が Functions の場合、コンテナ化方式の質問は省略し `container: "functions"` を自動設定する". Container question correctly skipped, `container: "functions"` auto-set.

**Questions that should be generated** (after extraction):

| # | Question | Source | Reason |
|---|---|---|---|
| 1 | Project name | Template (project_info) | Not in user request |
| 2 | Compute new/existing | Template (infra_config) | Not in user request |
| 3 | Sizing | Template (infra_config) | Not in user request |
| 4 | VCN config | Template (network) | Not in user request |
| 5 | Access method | Template (network) | Partially inferred via API GW, but enum not specified |

**Questions correctly skipped**: app_type (serverless), language (python), framework (flask), compute_type (functions), container (auto-set "functions"), demo purpose (poc), database (not mentioned), additional_services (object_storage + api_gateway extracted)

**Issues Found**:

2. **EDGE CASE: Sizing question irrelevant for Functions**. The sizing question asks about OCPU/memory for compute resources (1 OCPU/8GB, 2 OCPU/16GB, etc.). Functions don't have this kind of sizing -- they have per-invocation memory limits (128MB-2048MB). The skill has no rule to skip or adapt the sizing question for Functions. The sizing template answer options are Compute/CI-centric and don't apply. **New issue -- Functions-specific gap**.

3. **EDGE CASE: Access method question partially redundant**. The user said "APIゲートウェイ経由でアクセス" which strongly implies the access method. But the access_type enum (public/private/lb_public) doesn't have an "api_gateway" option. API Gateway is an additional_service, not an access_type. The access question should still be asked to determine whether API Gateway endpoint is public or private, but the current options (especially C = "ロードバランサー経由") are misleading for this scenario. **New issue -- Functions + API Gateway pattern not well modeled in access_type enum**.

4. **OBSERVATION: No database questions asked (correct)**. The user didn't mention any database need. The database category is correctly not activated. "画像リサイズ" (image resizing) doesn't inherently need a database. This is correct behavior.

---

### Phase 3-4: Answer Collection & Contradiction Detection

**Simulated Answers**:
- Project name: A (auto-generate) -> `"image-resize-api"`
- Compute new/existing: A (新規作成) -> `"new"`
- Sizing: A (最小構成) -> `"minimal"` (but irrelevant for Functions)
- VCN: A (新規VCN作成) -> `"new"`
- Access: A (パブリックアクセス) -> `"public"` (API Gateway itself is public)

**Contradiction check**: No contradictions found. Functions + no DB + Object Storage + API Gateway is a consistent serverless architecture. No cross-phase contradictions.

**Inference rules applied**:
- `access_type: "public"` -> `subnet_type: "public"` ... BUT Functions need a private subnet. The inference rule produces the wrong subnet_type for this scenario. Functions Application requires `subnet_ids` pointing to a private subnet for VCN connectivity. The skill's inference rule doesn't account for Functions always needing a private subnet regardless of access_type.

5. **ISSUE: subnet_type inference incorrect for Functions**. The rule `access_type: "public" -> subnet_type: "public"` is meant for compute/CI where the app itself sits in a public subnet. For Functions, the app (Functions Application) always sits in a private subnet, and public access is via API Gateway on a separate public subnet. The inference rule is compute-centric and produces wrong results for Functions. **New issue -- significant for correct Terraform generation**.

- `access_type: "public"` -> `load_balancer: false` -- Correct. Functions don't use OCI Load Balancer; they use API Gateway.

---

### Phase 5: Structured Output

**Clarity**: 5/5
**Completeness**: 4/5
**Correctness**: 4/5

**Required fields check (all 8)**:

| Field | Present | Value | Correct |
|---|---|---|---|
| `project_name` | Yes | `"image-resize-api"` | Yes |
| `app_type` | Yes | `"serverless"` | Yes |
| `compute_type` | Yes | `"functions"` | Yes |
| `compute_new_or_existing` | Yes | `"new"` | Yes |
| `language` | Yes | `"python"` | Yes |
| `framework` | Yes | `"flask"` | Yes |
| `container` | Yes | `"functions"` | Yes (auto-set) |
| `purpose` | Yes | `"poc"` | Yes |

**All 8 required fields present and correct.** PASS.

**Functions-specific edge cases**:

| Check | Result | Notes |
|---|---|---|
| No database field | Correct | User didn't request DB |
| No load_balancer | Correct | `load_balancer: false` |
| Object Storage in additional_services | Correct | `["object_storage", "api_gateway"]` |
| API Gateway in additional_services | Correct | Present |
| container = "functions" (auto-set) | Correct | Not "docker" or "none" |
| No sizing field | **Issue** | Should be omitted for Functions, but skill has no rule for this |

6. **ISSUE: sizing field handling for Functions**. The result.json from this test omits the `sizing` field entirely because Functions don't have traditional compute sizing. However, the skill doesn't explicitly say to omit sizing for Functions. If the sizing question is asked and answered "A) 最小構成", the result would include `sizing: { ocpu: 1, memory_gb: 8, shape: "VM.Standard.E4.Flex" }` which is meaningless for Functions. The skill should either skip the sizing question for Functions or document that sizing is N/A for Functions.

---

### Hearing Skill Summary Scores

| Phase | Clarity | Completeness | Correctness | Overall |
|---|---|---|---|---|
| Phase 1: Request Analysis | 5/5 | 4/5 | 5/5 | 4.7/5 |
| Phase 2: Question Generation | 4/5 | 4/5 | 5/5 | 4.3/5 |
| Phase 3-4: Collection & Contradiction | 5/5 | 4/5 | 4/5 | 4.3/5 |
| Phase 5: Structured Output | 5/5 | 4/5 | 4/5 | 4.3/5 |
| **Overall Average** | **4.75** | **4.0** | **4.5** | **4.4/5** |

---

## Part B: Generate-Terraform Skill Evaluation

### Phase 1: Resource Identification

**Clarity**: 5/5
**Completeness**: 5/5
**Correctness**: 5/5

**Resources correctly identified from result.json**:

| result.json field | OCI Resource | Terraform Resource | Correct |
|---|---|---|---|
| compute_type: functions | Functions Application | oci_functions_application | Yes |
| network.vcn: new | VCN + Subnets + Gateways | module "vcn" + oci_core_subnet | Yes |
| additional_services: object_storage | Object Storage Bucket | oci_objectstorage_bucket | Yes |
| additional_services: api_gateway | API Gateway + Deployment | oci_apigateway_gateway + oci_apigateway_deployment | Yes |

**Resources correctly NOT identified (absent from result.json)**:

| Resource | Reason for Exclusion | Correct |
|---|---|---|
| Database (ATP/MySQL) | No database field | Yes |
| Load Balancer | load_balancer: false | Yes |
| Compute Instance | compute_type != compute | Yes |
| OKE Cluster | compute_type != oke | Yes |
| Container Instance | compute_type != container_instances | Yes |

**Dependency chain**: VCN -> Subnets -> [Functions App (private), API Gateway (public), Object Storage] -> Outputs

---

### Phase 2: Terraform Code Generation

**Generated Files**:

| File | Generated | Notes |
|------|-----------|-------|
| provider.tf | Yes | No random provider (correct -- no DB) |
| variables.tf | Yes | Minimal vars -- no sizing, no DB, no SSH |
| terraform.tfvars | Yes | PLACEHOLDERs for all required vars |
| network.tf | Yes | VCN module v3.6.0, both subnets, both SLs |
| compute.tf | Yes | Functions Application on private subnet |
| additional.tf | Yes | Object Storage + API Gateway |
| outputs.tf | Yes | Functions + Object Storage + API GW outputs |
| database.tf | No (correct) | No DB in this scenario |
| lb.tf | No (correct) | No LB in this scenario |
| cloud-init.sh | No (correct) | Not needed for Functions |

#### Specific Check Results

**Check 1: terraform.tfvars with PLACEHOLDERs**
- `compartment_id = "PLACEHOLDER"` -- Yes
- `region = "PLACEHOLDER"` -- Yes
- `region_key = "PLACEHOLDER"` -- Yes
- `tenancy_namespace = "PLACEHOLDER"` -- Yes
- **Result**: PASS.

**Check 2: Functions compute template correct**
- `oci_functions_application.app` with `subnet_ids = [oci_core_subnet.private_subnet.id]` -- Yes
- Functions placed on private subnet -- Yes (correct for OCI Functions)
- `display_name = "${var.project_name}-fn-app"` follows naming convention -- Yes
- `freeform_tags` applied -- Yes
- Placeholder note for individual function definitions -- Yes
- **Result**: PASS. Matches template exactly.

**Check 3: Object Storage resource generated**
- `oci_objectstorage_bucket.images` -- Yes
- Uses `var.tenancy_namespace` for namespace -- Yes
- `access_type = "NoPublicAccess"` (secure default) -- Yes
- **Result**: PASS.

**Check 4: API Gateway resources generated**
- `oci_apigateway_gateway.gw` on public subnet -- Yes
- `endpoint_type = "PUBLIC"` -- Yes
- `oci_apigateway_deployment.api` with routes and ORACLE_FUNCTIONS_BACKEND -- Yes
- `function_id = "PLACEHOLDER_FUNCTION_ID"` (correct -- set after fn deploy) -- Yes
- **Result**: PASS.

**Check 5: Functions-specific outputs present**
- `functions_app_id` -- Yes (from oci_functions_application.app.id)
- **Result**: PASS.

**Check 6: OCIR output still generated**
- `ocir_repo_url` = `"${var.region_key}.ocir.io/${var.tenancy_namespace}/${var.project_name}"` -- Yes
- Functions use OCIR for container images, so this is correct even for serverless
- **Result**: PASS.

**Check 7: No DB-related resources or outputs**
- No database.tf generated -- Yes
- No `db_connection_string` output -- Yes
- No `db_ocid` output -- Yes
- No `random` provider in provider.tf -- Yes
- **Result**: PASS.

**Check 8: No LB-related resources or outputs**
- No lb.tf generated -- Yes
- No `lb_public_ip` output -- Yes
- No `lb_ocid` output -- Yes
- **Result**: PASS.

**Check 9: VCN module version pinned**
- `version = "3.6.0"` (exact, not `>=`) -- Yes
- **Result**: PASS.

**Check 10: Both security lists generated**
- Public SL with 80, 443, 8080 ingress -- Yes
- Private SL with VCN-internal all-protocol ingress -- Yes
- **Result**: PASS.

---

### Issues Found in Terraform Generation

#### ISSUE-IT3-01: No additional_services template for Object Storage or API Gateway
- **Severity**: Low (by design)
- **Description**: Unlike database and compute which have explicit templates in tf-templates/, there is no template for Object Storage or API Gateway. The skill provides a mapping table (additional_services -> Terraform Resource) but no HCL template. Agents must generate the HCL from OCI provider documentation knowledge.
- **Impact**: Low -- the resources are simple enough to generate correctly. But for consistency with other resource types, templates would help.
- **Recommendation**: Consider adding an `additional-services-template.md` with patterns for Object Storage, API Gateway, Streaming, and Logging.

#### ISSUE-IT3-02: API Gateway deployment has hardcoded route
- **Severity**: Expected (by design)
- **Description**: The API Gateway deployment includes a hardcoded `/resize` route with `ORACLE_FUNCTIONS_BACKEND` and `PLACEHOLDER_FUNCTION_ID`. This is specific to the image resize use case. In a generic scenario, the routes should be dynamically generated based on the application's API endpoints.
- **Impact**: Expected -- similar to Container Instance PLACEHOLDER_IMAGE_URL. The deploy-app skill will update this.
- **Recommendation**: None -- placeholder approach is consistent with the skill's design pattern.

#### ISSUE-IT3-03: Variables are minimal -- no sizing variables
- **Severity**: Observation (correct behavior)
- **Description**: variables.tf only has 5 variables (compartment_id, region, project_name, region_key, tenancy_namespace). No sizing variables because Functions don't use traditional compute sizing. This is correct but differs significantly from Iter1 (13 variables) and Iter2 (10 variables).
- **Impact**: None -- correct for this scenario.

#### ISSUE-IT3-04: API Gateway outputs go beyond the data contract
- **Severity**: Low (enhancement)
- **Description**: outputs.tf includes `api_gateway_id`, `api_gateway_hostname`, `api_gateway_deployment_id`, `object_storage_bucket`, `object_storage_namespace`. These are not in the outputs-template.md or the skill's output data contract. They are useful for deploy-app and verify skills but technically exceed the contract.
- **Impact**: Positive -- these outputs are needed by downstream skills. The output data contract should be expanded to cover additional_services outputs.
- **Recommendation**: Add additional_services output patterns to outputs-template.md.

---

### Generate-Terraform Summary Scores

| Dimension | Phase 1 | Phase 2 | Overall |
|-----------|---------|---------|---------|
| Clarity | 5/5 | 5/5 | 5/5 |
| Completeness | 5/5 | 4/5 | 4.5/5 |
| Correctness | 5/5 | 5/5 | 5/5 |

---

## Iter1 vs Iter2 vs Iter3 Comparison

### Hearing Skill

| Dimension | Iter1 | Iter2 | Iter3 | Trend |
|---|---|---|---|---|
| Clarity | 3.6 | 4.75 | 4.75 | Stable |
| Completeness | 3.2 | 4.5 | 4.0 | Slight dip (Functions gaps) |
| Correctness | 3.8 | 5.0 | 4.5 | Slight dip (subnet_type inference) |
| **Overall** | **3.5** | **4.8** | **4.4** | -0.4 from Iter2 |

**Analysis**: The Iter3 hearing score is slightly lower than Iter2 because this scenario exposed Functions-specific gaps that didn't exist for Compute/CI paths:
- Sizing question irrelevant for Functions
- subnet_type inference rule incorrect for Functions
- access_type enum doesn't model API Gateway access pattern
These are new coverage gaps, not regressions. The core improvements from Iter1->Iter2 (mapping table, required fields, container auto-skip) all held perfectly.

### Generate-Terraform Skill

| Dimension | Iter1 | Iter2 | Iter3 | Trend |
|---|---|---|---|---|
| Clarity | 3.5 | 4.5 | 5.0 | Improving |
| Completeness | 3.0 | 4.0 | 4.5 | Improving |
| Correctness | 4.0 | 4.5 | 5.0 | Improving |
| **Overall** | **~3.5** | **4.3** | **4.8** | +0.5 from Iter2 |

**Analysis**: Terraform generation scored highest in Iter3. The Functions path is simpler (fewer resources, fewer variables, no DB, no LB) which reduces the surface area for errors. The skill's template for Functions is clean and minimal. Object Storage and API Gateway were generated correctly despite having no dedicated templates.

---

## Cross-Iteration Issue Resolution Status

### Iter1 Critical Issues

| Issue | Iter2 Status | Iter3 Status |
|---|---|---|
| #1 No enum mapping table | RESOLVED | STILL RESOLVED (functions path works) |
| #3 Container auto-skip incomplete | RESOLVED | STILL RESOLVED (functions auto-set works) |
| #17 Required fields mismatch | RESOLVED | STILL RESOLVED (all 8 fields present) |
| #18 Missing `purpose` in required fields | RESOLVED | STILL RESOLVED |
| #14 OCI architecture contradiction | RESOLVED | NOT TESTED (no DB in this scenario) |
| #15 Cross-phase contradiction | RESOLVED | NOT TESTED (no contradictions) |
| #19 load_balancer default | RESOLVED | STILL RESOLVED (false for public) |

### Iter2 Issues

| Issue | Iter3 Status |
|---|---|
| IT2-01 MySQL password tfvars | NOT TESTED (no DB) |
| IT2-02 CI PLACEHOLDER image_url | NOT TESTED (no CI) |
| IT2-03 logging.tf retention_duration | NOT TESTED (no logging) |
| IT2-04 MySQL output pattern missing | NOT TESTED (no MySQL) |
| IT2-05 database-template display_name | NOT TESTED (no DB) |

---

## New Issues Discovered in Iter3

### Hearing Skill Issues

| ID | Severity | Description |
|---|---|---|
| IT3-H01 | Medium | **app_type precedence unclear**: When request matches both "api" and "serverless" patterns, no precedence rule exists |
| IT3-H02 | Medium | **Sizing question irrelevant for Functions**: No skip/adapt rule for Functions compute sizing |
| IT3-H03 | Medium | **subnet_type inference wrong for Functions**: `access_type: "public" -> subnet_type: "public"` is incorrect for Functions which always need private subnet |
| IT3-H04 | Low | **access_type enum lacks API Gateway pattern**: API GW access doesn't map cleanly to public/private/lb_public |
| IT3-H05 | Low | **sizing field in result.json undefined for Functions**: Should be omitted or have Functions-specific values |

### Generate-Terraform Skill Issues

| ID | Severity | Description |
|---|---|---|
| IT3-T01 | Low | **No templates for additional_services resources**: Object Storage, API Gateway, Streaming lack HCL templates |
| IT3-T02 | Low | **Output data contract doesn't cover additional_services**: api_gateway_hostname, object_storage_bucket not in contract |
| IT3-T03 | Observation | **API Gateway deployment route is scenario-specific**: Hardcoded /resize path; OK as placeholder |

---

## Improvement Suggestions for Future Iterations

### P0 - Should Fix (Hearing)

1. **Add Functions-specific rules to hearing skill**:
   - Skip sizing question when `compute_type = "functions"` (or adapt to Functions memory allocation: 128MB/256MB/512MB/1024MB)
   - Override subnet_type inference: `compute_type: "functions"` -> always `subnet_type: "private"` regardless of access_type
   - Document that Functions + API Gateway is the canonical serverless access pattern

2. **Add app_type precedence rule**: When multiple app_type patterns match (e.g., "API" + "serverless"), the more specific pattern wins. Suggest: if compute_type=functions, app_type defaults to "serverless" unless user explicitly says "Web" or "batch".

### P1 - Nice to Fix (Terraform)

3. **Add additional_services HCL templates**: Create `additional-services-template.md` with patterns for Object Storage, API Gateway, Streaming, Logging.

4. **Expand output data contract for additional_services**: Add `api_gateway_hostname`, `object_storage_bucket`, `streaming_endpoint` to the output contract so downstream skills have a stable interface.

### P2 - Polish

5. **Add access_type enum for API Gateway pattern**: Consider adding `"api_gateway"` to access_type enum, or document that API GW scenarios use `access_type: "public"` with API Gateway in additional_services.

6. **Document Functions sizing as N/A**: Add a note in result-schema.md that `sizing` field is not applicable when compute_type is "functions".

---

## Conclusion

### Iteration 3 Overall Assessment

| Skill | Score | vs Iter1 | vs Iter2 |
|---|---|---|---|
| Hearing | 4.4/5 | +0.9 | -0.4 |
| Generate-Terraform | 4.8/5 | +1.3 | +0.5 |
| **Combined** | **4.6/5** | **+1.1** | **+0.05** |

### Key Findings

1. **Terraform generation is strong**: The Functions path worked cleanly. The skill correctly handles the "no DB, no LB, minimal variables" scenario. Object Storage and API Gateway were generated correctly without dedicated templates. Score of 4.8/5.

2. **Hearing skill has Functions-specific gaps**: While the core extraction/mapping/required-fields improvements from Iter2 held perfectly, this scenario exposed 3 medium-severity gaps specific to the Functions/serverless path (sizing, subnet inference, app_type precedence). These are coverage gaps in a path not previously tested, not regressions.

3. **Three-iteration coverage**: Across all 3 iterations, we've now tested:
   - Iter1: Compute + ATP + Public (no LB, no additional services)
   - Iter2: Container Instances + MySQL + LB + Logging
   - Iter3: Functions + Object Storage + API Gateway (no DB, no LB)

   This covers all 4 compute_type paths (OKE untested), 2 of 2 DB types, LB and no-LB, and 3 of 4 additional_services.

4. **Remaining untested path**: OKE (Kubernetes) is the only compute_type not exercised. This is the most complex path (cluster + node pool + kubeconfig). Recommend testing in a future iteration.

### Scoring Trajectory

```
Hearing:             3.5 -> 4.8 -> 4.4  (peak at Iter2, dip due to new coverage gaps)
Generate-Terraform:  3.5 -> 4.3 -> 4.8  (steady improvement)
Combined:            3.5 -> 4.6 -> 4.6  (stable at high level)
```

The combined score has plateaued at 4.6/5. To reach 5.0, the remaining gaps are:
- Functions-specific hearing rules (P0 fixes above)
- Additional services templates and output contracts (P1 fixes above)
- OKE path coverage (untested)
