# ============================================================
# Object Storage - セッションデータ、Terraform state等の永続化
# ============================================================

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "oci_objectstorage_bucket" "galley" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.current.namespace
  name           = "${local.name_prefix}-${random_string.bucket_suffix.result}"
  access_type    = "NoPublicAccess"
  versioning     = "Enabled"
}
