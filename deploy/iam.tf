# ============================================================
# IAM - Dynamic Groups & Policies
# ============================================================

# ------------------------------------------------------------
# Galley Container Instance 用 Dynamic Group
# (Resource Principal で instance-agent command を実行するため)
# ------------------------------------------------------------

resource "oci_identity_dynamic_group" "galley" {
  compartment_id = var.tenancy_ocid
  name           = "${local.name_prefix}-server-dg"
  description    = "Galley MCP Server (Container Instance)"
  matching_rule  = "resource.id = '${oci_container_instances_container_instance.galley.id}'"
}

# ------------------------------------------------------------
# Build Instance 用 Dynamic Group
# ------------------------------------------------------------

resource "oci_identity_dynamic_group" "build" {
  compartment_id = var.tenancy_ocid
  name           = "${local.name_prefix}-build-dg"
  description    = "Galley Build Instance"
  matching_rule  = "instance.id = '${oci_core_instance.build.id}'"
}

# ------------------------------------------------------------
# Galley Server Policy (Container Instance)
# - Build Instance への Run Command 実行権限
# - Object Storage への書き込み権限（ビルド用アプリコード）
# ------------------------------------------------------------

resource "oci_identity_policy" "galley" {
  compartment_id = var.compartment_ocid
  name           = "${local.name_prefix}-server-policy"
  description    = "Galley Server が Build Instance でコマンド実行し、Object Storage にアクセスする権限"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.galley.name} to manage instance-agent-command-family in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.galley.name} to read instances in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.galley.name} to manage objects in compartment id ${var.compartment_ocid} where target.bucket.name = '${oci_objectstorage_bucket.galley.name}'",
    "Allow dynamic-group ${oci_identity_dynamic_group.galley.name} to read buckets in compartment id ${var.compartment_ocid}",
  ]
}

# ------------------------------------------------------------
# Build Instance Policy
# - Object Storage からのアプリコード取得権限
# ------------------------------------------------------------

resource "oci_identity_policy" "build" {
  compartment_id = var.compartment_ocid
  name           = "${local.name_prefix}-build-policy"
  description    = "Galley Build Instance が Object Storage からアプリコードを取得する権限"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.build.name} to read objects in compartment id ${var.compartment_ocid} where target.bucket.name = '${oci_objectstorage_bucket.galley.name}'",
    "Allow dynamic-group ${oci_identity_dynamic_group.build.name} to read buckets in compartment id ${var.compartment_ocid} where target.bucket.name = '${oci_objectstorage_bucket.galley.name}'",
  ]
}
