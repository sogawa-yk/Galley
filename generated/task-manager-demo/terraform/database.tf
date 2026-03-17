# =============================================================================
# MySQL Database Service
# =============================================================================

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

locals {
  mysql_sizing = {
    minimal = {
      shape_name = "MySQL.VM.Standard.E4.1.8GB"
    }
    standard = {
      shape_name = "MySQL.VM.Standard.E4.2.32GB"
    }
    large = {
      shape_name = "MySQL.VM.Standard.E4.4.64GB"
    }
  }
}

resource "oci_mysql_mysql_db_system" "mysql" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "task-manager-db"
  shape_name          = local.mysql_sizing[var.db_sizing].shape_name
  subnet_id           = oci_core_subnet.private_subnet.id

  admin_username = var.mysql_admin_username
  admin_password = var.mysql_admin_password

  data_storage_size_in_gb = 50

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
