# Expected Output - Eコマースシナリオ

## Input
`expected_result_ecommerce.json` (from Unit 1 test)
- app_type: web
- compute_type: container_instances
- database.type: atp
- network.vcn: new, load_balancer: true

## Expected Generated Files

| File | Required | Key Resources |
|---|---|---|
| provider.tf | Yes | oci provider, no backend |
| variables.tf | Yes | compartment_id, region, project_name, ci_ocpus, ci_memory_gb |
| terraform.tfvars | Yes | project_name = "ecommerce-demo" |
| network.tf | Yes | vcn module, public/private subnet, security lists, gateways |
| compute.tf | Yes | oci_container_instances_container_instance (image_url=PLACEHOLDER) |
| database.tf | Yes | oci_database_autonomous_database (ATP, minimal) |
| lb.tf | Yes | oci_load_balancer_load_balancer |
| outputs.tf | Yes | vcn_id, subnet_ids, container_instance_id, db_connection_string, lb_public_ip |

## Validation Checks
- [ ] provider.tfにbackendブロックがないこと
- [ ] 全リソースにfreeform_tagsが設定されていること
- [ ] 命名規則: `${var.project_name}-*` が使われていること
- [ ] Container Instanceのimage_urlがPLACEHOLDERであること
- [ ] outputs.tfに後続ユニットが必要な情報が含まれていること
