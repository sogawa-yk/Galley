# =============================================================================
# ATP Admin Password
# =============================================================================

resource "random_password" "atp_admin_password" {
  length           = 16
  special          = true
  override_special = "_#"
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
  min_special      = 1
}

locals {
  atp_admin_password = coalesce(var.atp_admin_password, random_password.atp_admin_password.result)

  # sizing mapping
  atp_sizing = {
    minimal = {
      cpu_core_count           = 1
      data_storage_size_in_tbs = 1
    }
    standard = {
      cpu_core_count           = 2
      data_storage_size_in_tbs = 1
    }
    large = {
      cpu_core_count           = 4
      data_storage_size_in_tbs = 2
    }
  }
}

# =============================================================================
# Autonomous Transaction Processing Database
# =============================================================================

resource "oci_database_autonomous_database" "atp" {
  compartment_id           = var.compartment_id
  display_name             = var.db_name
  db_name                  = replace(var.db_name, "-", "")
  db_workload              = "OLTP"
  cpu_core_count           = local.atp_sizing[var.db_sizing].cpu_core_count
  data_storage_size_in_tbs = local.atp_sizing[var.db_sizing].data_storage_size_in_tbs
  admin_password           = local.atp_admin_password
  is_auto_scaling_enabled  = true

  # Place ATP in private subnet for security
  subnet_id          = oci_core_subnet.private_subnet.id
  nsg_ids            = []
  is_mtls_connection_required = false

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
