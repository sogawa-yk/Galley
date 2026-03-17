# --- Random Password for MySQL ---

resource "random_password" "mysql_admin_password" {
  length           = 16
  special          = true
  override_special = "_#"
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
  min_special      = 1
}

locals {
  mysql_admin_password = coalesce(var.mysql_admin_password, random_password.mysql_admin_password.result)

  # Sizing mapping
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

# --- MySQL Database Service ---

resource "oci_mysql_mysql_db_system" "mysql" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = var.db_name
  shape_name          = local.mysql_sizing[var.db_sizing].shape_name
  subnet_id           = oci_core_subnet.private_subnet.id

  admin_username = var.mysql_admin_username
  admin_password = local.mysql_admin_password

  data_storage_size_in_gb = 50

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
