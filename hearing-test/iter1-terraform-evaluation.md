# Iteration 1: generate-terraform Skill Evaluation

**Scenario**: Python/FastAPI + Compute Instance + ATP Database, Public Access, No LB
**Date**: 2026-03-17
**Input**: Simulated hearing result (inventory-api)
**Output**: `generated/inventory-api/terraform/`

---

## Generated Files

| File | Generated | Notes |
|------|-----------|-------|
| provider.tf | Yes | Matches template |
| variables.tf | Yes | Custom for scenario |
| terraform.tfvars | Yes | Values from hearing result |
| network.tf | Yes | VCN module + subnets + security lists |
| compute.tf | Yes | oci_core_instance with cloud-init |
| database.tf | Yes | ATP with sizing map |
| outputs.tf | Yes | All required outputs |
| cloud-init.sh | Yes | Docker install for compute |
| lb.tf | No (correct) | load_balancer: false |
| additional.tf | No (correct) | additional_services: [] |

---

## Phase 1 Evaluation: Resource Identification

### Ratings
- **Clarity**: 4/5
- **Completeness**: 3/5
- **Correctness**: 4/5

### Issues Found

#### ISSUE-P1-01: compute_type=compute variable naming inconsistency between skill and template
- **Severity**: Medium
- **Description**: The skill says to use `var.compute_ocpu`, `var.compute_memory_gb`, `var.compute_shape` but the compute template uses `var.vm_ocpus`, `var.vm_memory_gb`, `var.vm_shape`, `var.vm_image_id`. The skill instructions override the template, but this creates confusion about which to follow.
- **Impact**: Agent must reconcile conflicting guidance. Template and skill diverge.
- **Recommendation**: Update compute-templates.md to use `var.compute_*` naming consistent with the skill instructions, or explicitly note in the skill that template variable names should be renamed.

#### ISSUE-P1-02: No explicit guidance on cloud-init.sh generation
- **Severity**: Medium
- **Description**: The compute template references `file("${path.module}/cloud-init.sh")` but the skill never mentions generating a cloud-init.sh file. The skill says "cloud-initでDockerインストール" but doesn't list cloud-init.sh in the generated files list (Section Phase 2 file list).
- **Impact**: An agent might generate compute.tf referencing a nonexistent file.
- **Recommendation**: Add `cloud-init.sh` to the generated files list and provide guidance on what it should contain (Docker install, firewall rules, language runtime).

#### ISSUE-P1-03: database template uses `var.sizing` not `var.db_sizing`
- **Severity**: High
- **Description**: The database-template.md uses `local.atp_sizing[var.sizing]` but the skill explicitly says "DBサイジング: `var.db_sizing`... `var.sizing`は使用しない". The template directly contradicts the skill instruction.
- **Impact**: If an agent follows the template verbatim, it will use the wrong variable name.
- **Recommendation**: Update database-template.md to use `var.db_sizing` instead of `var.sizing`.

#### ISSUE-P1-04: Missing `random` provider declaration
- **Severity**: Medium
- **Description**: The database template uses `random_password` resource but neither the skill nor the provider template mentions adding the `hashicorp/random` provider to the `required_providers` block.
- **Impact**: Terraform init will fail without the random provider.
- **Recommendation**: Add `random` provider to provider.tf template or add a note to include it when database is requested.

#### ISSUE-P1-05: No private_sl template provided
- **Severity**: Low
- **Description**: The network template only provides the public security list pattern. Private security list rules must be inferred by the agent.
- **Impact**: Minor -- agents can reasonably infer private SL rules, but explicit guidance reduces variability.
- **Recommendation**: Add a private security list pattern to the network template.

---

## Phase 2 Evaluation: Terraform Code Generation

### Ratings
- **Clarity**: 3/5
- **Completeness**: 3/5
- **Correctness**: 4/5

### Issues Found

#### ISSUE-P2-01: `display_name` for database -- skill says use `database.name` but template uses project_name pattern
- **Severity**: Low
- **Description**: The skill says "display_nameにはresult.jsonの`database.name`を使用する" but the template uses `"${var.project_name}-atp"`. In this scenario, hearing result has `database.name: "inventory-db"` which should be used as display_name. This requires a `var.db_name` variable not mentioned in variable naming guidance.
- **Impact**: Agents must infer that a `db_name` variable is needed.
- **Recommendation**: Add `var.db_name` to the variable naming conventions section.

#### ISSUE-P2-02: Outputs template missing several required outputs from the data contract
- **Severity**: High
- **Description**: The output data contract (skill instructions) requires:
  - `compute_instance_id` -- NOT in outputs-template.md (only `compute_public_ip`)
  - `compute_private_ip` -- NOT in outputs-template.md
  - `db_ocid` -- NOT in outputs-template.md
  - `ocir_repo_url` -- NOT in outputs-template.md
  - `lb_ocid` -- NOT in outputs-template.md (LB section only has `lb_public_ip`)
  - `container_instance_subnet_id` -- NOT in outputs-template.md (has `container_instance_id` instead, which is not in the data contract)

  The outputs-template.md is significantly incomplete relative to the output data contract defined in the skill.
- **Impact**: Agents must reconcile the data contract with the template, leading to inconsistency.
- **Recommendation**: Update outputs-template.md to match the full output data contract exactly.

#### ISSUE-P2-03: Network module version pinning inconsistency
- **Severity**: Medium
- **Description**: The skill says "バージョンは固定してください（例: `version = "3.6.0"`）" with explicit warning against `>=`. But the network template uses `version = ">= 3.6.0"` which directly contradicts the skill instruction.
- **Impact**: Template contradicts skill. Agent must decide which to follow.
- **Recommendation**: Fix network-template.md to use exact version pinning: `version = "3.6.0"`.

#### ISSUE-P2-04: No SSH key variable for compute instances
- **Severity**: Medium
- **Description**: For compute_type=compute with public access, SSH access is expected but there is no SSH key variable (`ssh_authorized_keys`) in either the template or skill. Without this, the instance is unreachable.
- **Impact**: Generated compute instance cannot be accessed via SSH.
- **Recommendation**: Add `var.ssh_public_key` variable and include it in `metadata` block of compute instance.

#### ISSUE-P2-05: ATP subnet placement not specified
- **Severity**: Medium
- **Description**: The skill does not specify whether ATP should be placed in a public or private subnet. The template doesn't include `subnet_id` at all. For a demo/PoC with public compute, ATP should typically go in a private subnet with private endpoint access.
- **Impact**: Agent must make an architectural decision without guidance. If ATP has no subnet_id, it gets a public endpoint by default, which is a security concern.
- **Recommendation**: Add guidance on ATP subnet placement. For `network.access_type: public` scenarios, recommend private subnet with private endpoint.

#### ISSUE-P2-06: No guidance on application port in security list
- **Severity**: Low
- **Description**: The skill says the template generates security lists but doesn't specify what application port to open based on `framework`. FastAPI default is 8000, Express is 3000, Flask is 5000, etc. The network template only opens 80/443.
- **Impact**: Agent must infer which ports to open based on framework knowledge.
- **Recommendation**: Add a framework-to-port mapping table or note that the application port should be opened in the security list.

#### ISSUE-P2-07: `region_key` and `tenancy_namespace` variables for OCIR not in skill guidance
- **Severity**: Medium
- **Description**: The skill mentions OCIR output format `{region_key}.ocir.io/{tenancy_namespace}/{project_name}` but doesn't list `region_key` or `tenancy_namespace` as required variables. These need to be defined somewhere.
- **Impact**: Agent must infer these variables are needed.
- **Recommendation**: Add these to the variables section of the skill, or provide a data source pattern to auto-detect them.

#### ISSUE-P2-08: Database `db_name` character restrictions not documented
- **Severity**: Low
- **Description**: ATP `db_name` field only allows alphanumeric characters (no hyphens). The template does `replace(var.project_name, "-", "")` but if using `database.name` ("inventory-db"), the same transform is needed. This is implicit, not explicit.
- **Impact**: Minor -- agents familiar with OCI will know this, but it should be documented.
- **Recommendation**: Note the `db_name` alphanumeric restriction in the skill or template.

---

## Output Data Contract Compliance

| Required Output | Present | Notes |
|----------------|---------|-------|
| `vcn_id` | Yes | via module.vcn.vcn_id |
| `public_subnet_id` | Yes | |
| `private_subnet_id` | Yes | |
| `compute_instance_id` | Yes | Added (not in template) |
| `compute_public_ip` | Yes | |
| `compute_private_ip` | Yes | Added (not in template) |
| `db_connection_string` (sensitive) | Yes | |
| `db_ocid` | Yes | Added (not in template) |
| `ocir_repo_url` | Yes | Added (not in template) |
| `lb_public_ip` | N/A | No LB in this scenario |
| `lb_ocid` | N/A | No LB in this scenario |
| `oke_cluster_id` | N/A | compute_type=compute |
| `oke_kubeconfig` | N/A | compute_type=compute |
| `container_instance_subnet_id` | N/A | compute_type=compute |
| `functions_app_id` | N/A | compute_type=compute |

**Result**: All applicable outputs present. 4 outputs required interpolation beyond what the template provides.

---

## Scenario-Specific Checks

| Check | Result | Notes |
|-------|--------|-------|
| compute_type=compute handled? | Yes | oci_core_instance generated correctly |
| ATP database handled? | Yes | With sizing map and random password |
| No load balancer handled? | Yes | lb.tf correctly omitted |
| Public access handled? | Yes | Public subnet, public IP assigned |
| Variable naming (compute_*) | Yes | Followed skill over template |
| Variable naming (db_sizing) | Yes | Followed skill over template |
| Naming convention ({project}-{type}) | Yes | All resources follow pattern |
| Freeform tags on all resources | Yes | All resources tagged |
| No backend block | Yes | Correct for Resource Manager |
| VCN module version pinned | Yes | Used exact "3.6.0" per skill |

---

## Summary of Issues by Severity

| Severity | Count | Issues |
|----------|-------|--------|
| High | 2 | P1-03 (db template var.sizing), P2-02 (outputs template incomplete) |
| Medium | 5 | P1-01 (compute var naming), P1-02 (cloud-init missing), P1-04 (random provider), P2-03 (VCN version), P2-04 (SSH key), P2-05 (ATP subnet), P2-07 (OCIR vars) |
| Low | 3 | P1-05 (private_sl), P2-01 (db_name var), P2-06 (app port), P2-08 (db_name chars) |

---

## Overall Ratings

| Dimension | Phase 1 | Phase 2 | Overall |
|-----------|---------|---------|---------|
| Clarity | 4/5 | 3/5 | 3.5/5 |
| Completeness | 3/5 | 3/5 | 3/5 |
| Correctness | 4/5 | 4/5 | 4/5 |

---

## Top Improvements (Priority Order)

1. **Fix template-skill inconsistencies**: database-template.md (`var.sizing` -> `var.db_sizing`), compute-templates.md (`var.vm_*` -> `var.compute_*`), network-template.md (version pinning)
2. **Complete outputs-template.md**: Add all outputs from the data contract (`compute_instance_id`, `compute_private_ip`, `db_ocid`, `ocir_repo_url`, `lb_ocid`, `container_instance_subnet_id`)
3. **Add cloud-init.sh to generated files list**: The skill should explicitly list it and describe expected contents
4. **Add random provider to provider template**: When database is used
5. **Add SSH key variable**: For compute_type=compute scenarios
6. **Add OCIR variables to skill**: `region_key` and `tenancy_namespace` should be listed as required variables
7. **Add ATP subnet placement guidance**: Recommend private subnet for database security
8. **Add framework-to-port mapping**: Help agents determine which ports to open in security lists
