# Expected Output - APIサーバーシナリオ

## Input
`expected_result_api.json` (from Unit 1 test)
- app_type: api
- compute_type: oke
- database.type: none
- network.vcn: new, load_balancer: true

## Expected Generated Files

| File | Required | Key Resources |
|---|---|---|
| provider.tf | Yes | oci provider, no backend |
| variables.tf | Yes | compartment_id, region, project_name, node_shape, node_ocpus, node_memory_gb, node_count |
| terraform.tfvars | Yes | project_name = "api-server-test" |
| network.tf | Yes | vcn module, public/private subnet, security lists, gateways |
| compute.tf | Yes | oke module (cluster + node pool) |
| database.tf | No | database.type = none |
| lb.tf | Yes | oci_load_balancer_load_balancer |
| outputs.tf | Yes | vcn_id, subnet_ids, oke_cluster_id, oke_kubeconfig, lb_public_ip |

## Validation Checks
- [ ] database.tfが生成されていないこと
- [ ] OKEに公式モジュール（terraform-oci-oke）が使われていること
- [ ] VCNに公式モジュール（terraform-oci-vcn）が使われていること
- [ ] ノードプールのsizingがresult.jsonのsizingフィールドと一致すること
