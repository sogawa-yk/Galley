# Iteration 2: Combined Evaluation Report (Hearing + Generate-Terraform)

**Scenario**: Node.js/Express + Container Instances + MySQL + Load Balancer + Logging
**Date**: 2026-03-17
**User Request**: 「社内向けのチケット管理システムのデモ環境を作りたい。Node.js/Expressで、Container Instancesにデプロイ。MySQLデータベース使用。ロードバランサー経由でパブリックアクセス。ログイン認証機能あり。Logging/Monitoringも欲しい。」

---

## Part A: Hearing Skill Evaluation

### Phase 1: Request Analysis

**Clarity**: 5/5
**Completeness**: 4/5
**Correctness**: 5/5

**Extracted values using the NEW enum mapping table**:

| Field | Extracted Value | Source Text | Mapping Entry Used |
|---|---|---|---|
| app_type | `"web"` | チケット管理システム | app_type: Webアプリ -> `"web"` |
| language | `"nodejs"` | Node.js/Express | Direct (schema example) |
| framework | `"express"` | Node.js/Express | Direct (schema example) |
| compute_type | `"container_instances"` | Container Instancesにデプロイ | compute_type: Container Instances -> `"container_instances"` |
| database.type | `"mysql"` | MySQLデータベース使用 | database.type: MySQL -> `"mysql"` |
| network.access_type | `"lb_public"` | ロードバランサー経由でパブリックアクセス | Inferred (skill inference rules) |
| additional_services | `["logging"]` | Logging/Monitoringも欲しい | additional_services mapping table |

**Improvement from Iter1**: The enum mapping table (new in Iter2) resolved the ambiguity flagged as Iter1 Critical Issue #1. For this scenario, `"container_instances"` was directly in the mapping table -- no guessing required. `"mysql"` was also directly mapped. This is a clear improvement.

**Remaining Issues**:

1. **MINOR: `purpose` extraction ambiguity persists**. User said 「デモ環境」 and 「社内向け」. The mapping table has `"顧客デモ / 製品デモ" -> "customer_demo"` and `"トレーニング / ハンズオン" -> "training"`. 「社内向けデモ」 does not exactly match any entry. It is closest to `"customer_demo"` (internal demo for stakeholders) but could also be `"training"`. The mapping table does not cover 「社内デモ」 as a distinct phrase. **Not a regression** -- Iter1 also lacked this, and the mapping table is an improvement overall.

2. **MINOR: `load_balancer` and `access_type` inference**. The user said 「ロードバランサー経由でパブリックアクセス」 which clearly maps to `access_type: "lb_public"`. The inference rule `access_type: "lb_public" -> load_balancer: true` correctly defaults load_balancer. This worked well -- the inference rules added in Iter2 are effective.

---

### Phase 2: Question Generation

**Clarity**: 4/5
**Completeness**: 5/5
**Correctness**: 5/5

**Questions that should be generated** (after extraction):

| # | Question | Source | Reason |
|---|---|---|---|
| 1 | Project name | Template (project_info) | Not in user request |
| 2 | Demo purpose | Template (project_info) | 「デモ環境」 is ambiguous between enum values |
| 3 | Container method | Template (app_type) | CI requires asking (skill rule: "Functions以外は必ず提示する") |
| 4 | Compute new/existing | Template (infra_config) | Not in user request |
| 5 | Sizing | Template (infra_config) | Not in user request |
| 6 | VCN config | Template (network) | Not in user request |
| 7 | Sample data (dynamic) | Dynamic | Demo needs sample data |
| 8 | Frontend approach (dynamic) | Dynamic | Web app needs frontend clarification |

**Questions correctly skipped**: app_type (web extracted), language (nodejs extracted), compute_type (container_instances extracted), database type (mysql extracted), access method (lb_public extracted), additional_services (logging extracted)

**Key Test: Container question for Container Instances**:
The skill says: "コンピュート種別が Functions 以外（Compute/OKE/Container Instances）の場合、コンテナ化方式の質問は必ず提示する". For Container Instances, this means the container question IS asked even though "Container Instances" strongly implies Docker. This is correct behavior -- the user might want to confirm Docker vs. a specific container runtime.

**Improvement from Iter1**: The container question handling rule (Iter1 Critical Issue #3) is now explicit. The rule clearly states Functions is the only auto-skip case. For Container Instances, the question is correctly presented. This resolves the ambiguity.

**Remaining Issue**:

3. **OBSERVATION: Container question feels redundant for CI**. While technically correct to ask, Container Instances *requires* Docker containers. Answering "B) コンテナ不要" would be contradictory with `compute_type: container_instances`. The Phase 4 contradiction detection should catch this, but it would be more efficient to auto-set `container: "docker"` for CI and skip the question. This is a design choice, not a bug.

---

### Phase 3-4: Answer Collection & Contradiction Detection

**Simulated Answers**:
- Project name: A (auto-generate) -> `"ticket-system-demo"`
- Purpose: A (顧客向け製品デモ) -> `"customer_demo"`
- Container: A (Docker) -> `"docker"`
- Compute new/existing: A (新規作成) -> `"new"`
- Sizing: A (最小構成) -> `"minimal"`
- VCN: A (新規VCN作成) -> `"new"`
- Sample data: Yes, basic ticket data + admin/user accounts
- Frontend: Server-side rendered (Express + template engine)

**Contradiction check**: No contradictions found. Container Instances + Docker + private subnet + LB is a consistent architecture. MySQL on private subnet with CI on private subnet allows direct VCN communication.

**Improvement from Iter1**: The cross-phase contradiction rule (new in Iter2: "Phase 1で抽出した値とPhase 3の回答が矛盾する場合も検出対象") addresses Iter1 Issue #15. Also the OCI-specific contradiction pattern for public + ATP is now documented (Iter1 Issue #14). Neither applies to this scenario but the coverage is improved.

---

### Phase 5: Structured Output

**Clarity**: 5/5
**Completeness**: 5/5
**Correctness**: 5/5

**Required fields check (all 8)**:

| Field | Present | Value | Correct |
|---|---|---|---|
| `project_name` | Yes | `"ticket-system-demo"` | Yes |
| `app_type` | Yes | `"web"` | Yes |
| `compute_type` | Yes | `"container_instances"` | Yes |
| `compute_new_or_existing` | Yes | `"new"` | Yes |
| `language` | Yes | `"nodejs"` | Yes |
| `framework` | Yes | `"express"` | Yes |
| `container` | Yes | `"docker"` | Yes |
| `purpose` | Yes | `"customer_demo"` | Yes |

**All 8 required fields present and correct.**

**Improvement from Iter1**: The required fields mismatch (Iter1 Critical Issues #17, #18) is resolved. hearing.md Phase 5 now lists all 8 required fields including `container` and `purpose`, matching result-schema.md.

**Inference rules check**:

| Rule | Input | Output | Correct |
|---|---|---|---|
| subnet_type from access_type | `lb_public` | `"private"` | Yes (app behind LB in private subnet) |
| load_balancer from access_type | `lb_public` | `true` | Yes |
| database.sizing from compute sizing | `minimal` compute | `"minimal"` DB | Yes |

**Improvement from Iter1**: The `load_balancer` default is now explicitly defined for all access_type values (Iter1 Issue #19). For `"lb_public" -> true`, for `"public"/"private" -> false`. Clear and unambiguous.

---

### Hearing Skill Summary Scores

| Phase | Clarity | Completeness | Correctness | Overall |
|---|---|---|---|---|
| Phase 1: Request Analysis | 5/5 | 4/5 | 5/5 | 4.7/5 |
| Phase 2: Question Generation | 4/5 | 5/5 | 5/5 | 4.7/5 |
| Phase 3-4: Collection & Contradiction | 5/5 | 4/5 | 5/5 | 4.7/5 |
| Phase 5: Structured Output | 5/5 | 5/5 | 5/5 | 5.0/5 |
| **Overall Average** | **4.75** | **4.5** | **5.0** | **4.8/5** |

**Iter1 Overall**: 3.5/5 -> **Iter2 Overall**: 4.8/5 (+1.3 improvement)

---

## Part B: Generate-Terraform Skill Evaluation

### Phase 1: Resource Identification

**Clarity**: 5/5
**Completeness**: 4/5
**Correctness**: 5/5

**Resources correctly identified from result.json**:

| result.json field | OCI Resource | Terraform Resource | Correct |
|---|---|---|---|
| compute_type: container_instances | Container Instance | oci_container_instances_container_instance | Yes |
| database.type: mysql | MySQL DB System | oci_mysql_mysql_db_system | Yes |
| network.vcn: new | VCN + Subnets + Gateways | module "vcn" + oci_core_subnet | Yes |
| network.load_balancer: true | Load Balancer | oci_load_balancer_load_balancer | Yes |
| additional_services: logging | Log Group + Custom Log | oci_logging_log_group + oci_logging_log | Yes |

**Dependency chain**: VCN -> Subnets -> [CI (private), MySQL (private), LB (public)] -> Outputs

---

### Phase 2: Terraform Code Generation

**Generated Files**:

| File | Generated | Notes |
|------|-----------|-------|
| provider.tf | Yes | Includes `random` provider for MySQL password |
| variables.tf | Yes | Uses `var.db_sizing` (not `var.sizing`) |
| terraform.tfvars | Yes | PLACEHOLDERs for all required vars |
| network.tf | Yes | VCN module v3.6.0, both subnets, both SLs |
| compute.tf | Yes | Container Instance on private subnet |
| database.tf | Yes | MySQL with sizing map, random password |
| lb.tf | Yes | LB + backend set + listener |
| logging.tf | Yes | Log group + custom log |
| outputs.tf | Yes | All data contract outputs |
| cloud-init.sh | No (correct) | Not needed for Container Instances |

#### Specific Check Results

**Check 1: terraform.tfvars with PLACEHOLDERs**
- `compartment_id = "PLACEHOLDER"` -- Yes
- `region = "PLACEHOLDER"` -- Yes
- `region_key = "PLACEHOLDER"` -- Yes
- `tenancy_namespace = "PLACEHOLDER"` -- Yes
- **Result**: PASS. All required vars have PLACEHOLDERs.

**Check 2: `var.db_sizing` used (not `var.sizing`)**
- database.tf uses `local.mysql_sizing[var.db_sizing]` -- Yes
- variables.tf defines `variable "db_sizing"` -- Yes
- **Result**: PASS. Iter1 Issue P1-03 is resolved.

**Check 3: Outputs complete per data contract**

| Required Output | Present | Source |
|---|---|---|
| `vcn_id` | Yes | module.vcn.vcn_id |
| `public_subnet_id` | Yes | oci_core_subnet.public_subnet.id |
| `private_subnet_id` | Yes | oci_core_subnet.private_subnet.id |
| `container_instance_subnet_id` | Yes | oci_core_subnet.private_subnet.id |
| `db_connection_string` (sensitive) | Yes | mysql endpoints hostname |
| `db_ocid` | Yes | mysql.id |
| `lb_public_ip` | Yes | lb.ip_addresses[0] |
| `lb_ocid` | Yes | lb.id |
| `ocir_repo_url` | Yes | Constructed from vars |
- **Result**: PASS. All applicable outputs present. (Iter1 Issue P2-02 improvement -- outputs template now has complete listings.)

**Check 4: Random provider for MySQL password**
- provider.tf includes `hashicorp/random >= 3.5.0` -- Yes
- database.tf uses `random_password.mysql_admin_password` -- Yes
- **Result**: PASS. Iter1 Issue P1-04 is resolved.

**Check 5: lb.tf generated for container_instances + load_balancer**
- lb.tf generated with LB on public subnet -- Yes
- Skill rule: "compute_type: container_instances の場合のみTerraform管理のLBを生成" -- Followed correctly
- Backend set health check on port 8080 -- Yes
- **Result**: PASS. This is a NEW scenario not tested in Iter1.

**Check 6: VCN module version exactly "3.6.0"**
- network.tf: `version = "3.6.0"` -- Yes (not `>= 3.6.0`)
- **Result**: PASS. Iter1 Issue P2-03 is resolved.

**Check 7: Private security list template available**
- network-template.md now includes `oci_core_security_list "private_sl"` section -- Yes
- network.tf correctly generates both public_sl and private_sl -- Yes
- **Result**: PASS. Iter1 Issue P1-05 is resolved.

**Check 8: Container Instance on private subnet (lb_public access)**
- compute.tf: `subnet_id = oci_core_subnet.private_subnet.id` -- Yes
- Skill rule: "lb_public または private -> プライベートサブネット" -- Followed correctly
- **Result**: PASS.

---

### Remaining Issues Found

#### ISSUE-IT2-01: MySQL password variable defaults to null but tfvars omits it
- **Severity**: Low
- **Description**: `var.mysql_admin_password` has `default = null` in variables.tf and is not in terraform.tfvars (commented out). This is correct behavior (random password is generated), but a terraform plan would show the random password resource being created without any warning. Some teams might want to explicitly set a password.
- **Impact**: None for functionality. Documentation/UX concern only.
- **Recommendation**: Add a comment in tfvars explaining the auto-generation behavior (already done).

#### ISSUE-IT2-02: Container Instance image_url is PLACEHOLDER
- **Severity**: Expected (by design)
- **Description**: The `image_url = "PLACEHOLDER_IMAGE_URL"` in compute.tf is correct per skill design (deploy-app sets this later). However, terraform plan will fail with this placeholder since it's not a valid image URL.
- **Impact**: Expected -- this is documented in the skill. Terraform apply requires deploy-app to update this first.
- **Recommendation**: None -- this is by design. Consider adding a `# TODO: Replace with OCIR image URL after docker push` comment (already present).

#### ISSUE-IT2-03: logging.tf `retention_duration` may not be a valid argument
- **Severity**: Medium
- **Description**: `oci_logging_log` resource's `retention_duration` attribute may not exist in the OCI Terraform provider. The correct attribute for log retention might be configured at the log group level or via a different parameter. The OCI provider documentation should be consulted.
- **Impact**: Potential terraform plan failure on this specific attribute.
- **Recommendation**: Verify against OCI Terraform provider docs. Consider removing or using the correct attribute name.

#### ISSUE-IT2-04: MySQL db_connection_string output uses endpoints[0].hostname
- **Severity**: Low
- **Description**: `oci_mysql_mysql_db_system.mysql.endpoints[0].hostname` is the correct way to get the MySQL hostname, but the outputs-template.md shows an ATP-style connection string pattern. For MySQL, the connection string format differs (hostname:port vs ATP connection string).
- **Impact**: The output works but the template example is ATP-specific and may mislead agents.
- **Recommendation**: Add a MySQL-specific output pattern to outputs-template.md.

#### ISSUE-IT2-05: No db_name variable for MySQL display_name in template
- **Severity**: Low (resolved by skill instruction)
- **Description**: The database-template.md for MySQL uses `"${var.project_name}-mysql"` for display_name but the skill says to use `var.db_name`. The generated code correctly uses `var.db_name` following the skill instruction over the template.
- **Impact**: Template and skill still diverge for display_name. Agent must follow skill.
- **Recommendation**: Update database-template.md to use `var.db_name`.

---

### Generate-Terraform Summary Scores

| Dimension | Phase 1 | Phase 2 | Overall |
|-----------|---------|---------|---------|
| Clarity | 5/5 | 4/5 | 4.5/5 |
| Completeness | 4/5 | 4/5 | 4/5 |
| Correctness | 5/5 | 4/5 | 4.5/5 |

**Iter1 Terraform Overall**: ~3.5/5 -> **Iter2 Terraform Overall**: 4.3/5 (+0.8 improvement)

---

## Iter1 vs Iter2 Comparison Summary

### Hearing Skill

| Dimension | Iter1 | Iter2 | Delta |
|---|---|---|---|
| Clarity | 3.6 | 4.75 | +1.15 |
| Completeness | 3.2 | 4.5 | +1.3 |
| Correctness | 3.8 | 5.0 | +1.2 |
| **Overall** | **3.5** | **4.8** | **+1.3** |

### Generate-Terraform Skill

| Dimension | Iter1 | Iter2 | Delta |
|---|---|---|---|
| Clarity | 3.5 | 4.5 | +1.0 |
| Completeness | 3.0 | 4.0 | +1.0 |
| Correctness | 4.0 | 4.5 | +0.5 |
| **Overall** | **~3.5** | **4.3** | **+0.8** |

---

## Iter1 Critical Issues Resolution Status

### Hearing Skill Issues

| Iter1 Issue | Status | Evidence |
|---|---|---|
| #1 No enum mapping table | **RESOLVED** | New mapping table in hearing.md Phase 1 covers all common values |
| #3 Container auto-skip rules incomplete | **RESOLVED** | Explicit rule: "Functions以外は必ず提示する" |
| #17 Required fields mismatch (hearing.md vs schema) | **RESOLVED** | hearing.md Phase 5 now lists all 8 required fields |
| #18 Missing `purpose` in required fields | **RESOLVED** | `purpose` now listed in required fields |
| #14 OCI architecture contradiction (public+ATP) | **RESOLVED** | New OCI-specific contradiction pattern added |
| #15 Cross-phase contradiction | **RESOLVED** | New "クロスフェーズ矛盾" detection rule added |
| #19 load_balancer default undefined | **RESOLVED** | Inference rules table now covers all access_type values |

### Generate-Terraform Skill Issues

| Iter1 Issue | Status | Evidence |
|---|---|---|
| P1-03 Template uses var.sizing not var.db_sizing | **RESOLVED** | database-template.md now uses `var.db_sizing` |
| P1-04 Random provider missing | **RESOLVED** | Skill now explicitly says to add random provider for DB |
| P1-05 No private_sl template | **RESOLVED** | network-template.md now includes private SL pattern |
| P2-02 Outputs template incomplete | **PARTIALLY RESOLVED** | Added container_instance_subnet_id, db_ocid, lb_ocid, ocir_repo_url. MySQL output pattern still missing. |
| P2-03 VCN module version not pinned | **RESOLVED** | network-template.md uses exact `"3.6.0"` |
| P2-04 SSH key variable missing | **RESOLVED** | Skill now documents `var.ssh_public_key` for compute |
| P2-05 ATP subnet placement | **RESOLVED** | Skill now has "ATPサブネット配置ガイダンス" |
| P2-06 App port not in security list | **RESOLVED** | Skill now says "セキュリティリストのアプリポートは8080を開放" |
| P2-07 OCIR variables not documented | **RESOLVED** | `var.region_key` and `var.tenancy_namespace` now in skill |
| P1-01 Compute var naming inconsistency | **NOT TESTED** | This scenario uses CI, not Compute. Check in Iter3 if template updated. |
| P1-02 cloud-init.sh not in file list | **RESOLVED** | Skill now lists cloud-init.sh in generated files |
| P2-01 db_name variable | **RESOLVED** | `var.db_name` now documented in skill variable naming section |
| P2-08 db_name character restriction | **RESOLVED** | Skill now documents `replace(var.db_name, "-", "")` for ATP |

---

## New Issues Discovered in Iter2

| ID | Severity | Description |
|---|---|---|
| IT2-01 | Low | MySQL password tfvars documentation (cosmetic) |
| IT2-02 | Expected | Container Instance PLACEHOLDER image_url (by design) |
| IT2-03 | Medium | logging.tf `retention_duration` may not be valid OCI provider attribute |
| IT2-04 | Low | MySQL-specific output pattern missing from outputs-template.md |
| IT2-05 | Low | database-template.md still uses project_name for display_name, not var.db_name |

---

## Improvement Suggestions for Iter3

### P0 - Should Fix
1. **Add MySQL output pattern to outputs-template.md**: Currently only ATP pattern exists. MySQL uses `endpoints[0].hostname` which is different.
2. **Verify logging.tf attribute names**: Confirm `retention_duration` is valid for `oci_logging_log` resource in OCI provider.

### P1 - Nice to Fix
3. **Consider auto-setting container=docker for Container Instances**: Since CI requires Docker, the container question is technically redundant. Add a new auto-set rule: "compute_type=container_instances -> container: docker (auto-set, skip question)".
4. **Add 「社内デモ」 to purpose mapping table**: Map to `"customer_demo"` or add a new enum value.
5. **Update database-template.md to use var.db_name for display_name**: Consistent with skill instructions.

### P2 - Polish
6. **Add additional_services logging template**: Currently no template exists for logging resources. Agents must generate from the resource mapping table alone.
7. **Consider adding Monitoring service alongside Logging**: User requested "Logging/Monitoring" but only logging was generated. OCI Monitoring (alarms, metrics) is a separate service.

---

## Conclusion

Iteration 2 shows significant improvement across both skills:

- **Hearing Skill**: +1.3 points (3.5 -> 4.8). The enum mapping table, inference rules, and required fields synchronization resolved all 3 critical issues from Iter1. The skill is now highly reliable for extracting structured data from natural language requests.

- **Generate-Terraform Skill**: +0.8 points (~3.5 -> 4.3). Template-skill inconsistencies (var.sizing, VCN version pinning, missing outputs) are largely resolved. The new scenario successfully tested Container Instances, MySQL, Load Balancer, and Logging -- all of which were not covered in Iter1.

- **Key remaining gap**: Template files still lag behind skill instructions in some areas (MySQL output pattern, db_name for display_name). The pattern of "skill says X but template says Y" is reduced but not eliminated.

- **New coverage**: This scenario validated 4 new resource types (Container Instances, MySQL, Load Balancer, Logging) that were not exercised in Iter1's Compute + ATP scenario.
