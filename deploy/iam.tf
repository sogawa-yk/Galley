# # ============================================================
# # IAM Policy - 最小権限原則に従った権限付与
# # ============================================================
# # 動的グループは利用者が事前に作成済みのものを使用（var.dynamic_group_id）
# # ポリシーはコンパートメントレベルで作成
# # orasejapanの場合、ポリシーの設定は不要

# resource "oci_identity_policy" "galley" {
#   compartment_id = var.compartment_ocid
#   name           = "${local.name_prefix}-policy"
#   description    = "Permissions for Galley MCP server"
#   statements = [
#     # Object Storage: Galleyバケットへの管理権限
#     "Allow dynamic-group id ${var.dynamic_group_id} to manage objects in compartment id ${var.compartment_ocid} where target.bucket.name = '${oci_objectstorage_bucket.galley.name}'",
#     "Allow dynamic-group id ${var.dynamic_group_id} to read buckets in compartment id ${var.compartment_ocid} where target.bucket.name = '${oci_objectstorage_bucket.galley.name}'",

#     # Resource Manager: 作業対象コンパートメントでのスタック管理
#     "Allow dynamic-group id ${var.dynamic_group_id} to manage orm-stacks in compartment id ${local.work_compartment_id}",
#     "Allow dynamic-group id ${var.dynamic_group_id} to manage orm-jobs in compartment id ${local.work_compartment_id}",

#     # VCN/Subnet: 作業対象コンパートメントでのネットワーク管理
#     "Allow dynamic-group id ${var.dynamic_group_id} to manage virtual-network-family in compartment id ${local.work_compartment_id}",

#     # Compute: 作業対象コンパートメントでのインスタンス管理
#     "Allow dynamic-group id ${var.dynamic_group_id} to manage instance-family in compartment id ${local.work_compartment_id}",

#     # Container Instances: 読み取り権限
#     "Allow dynamic-group id ${var.dynamic_group_id} to read container-instances in compartment id ${local.work_compartment_id}",
#   ]
# }
