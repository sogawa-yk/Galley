# Database Templates

## ATP (Autonomous Transaction Processing) — 動的生成パターン

```hcl
resource "random_password" "atp_admin_password" {
  length           = 16
  special          = true
  override_special = "_#"
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
  min_special      = 1
}

variable "atp_admin_password" {
  description = "Admin password for ATP. If not set, a random password is generated."
  type        = string
  sensitive   = true
  default     = null
}

locals {
  atp_admin_password = coalesce(var.atp_admin_password, random_password.atp_admin_password.result)

  # sizing マッピング
  atp_sizing = {
    minimal = {
      cpu_core_count            = 1
      data_storage_size_in_tbs  = 1
    }
    standard = {
      cpu_core_count            = 2
      data_storage_size_in_tbs  = 1
    }
    large = {
      cpu_core_count            = 4
      data_storage_size_in_tbs  = 2
    }
  }
}

resource "oci_database_autonomous_database" "atp" {
  compartment_id              = var.compartment_id
  display_name                = var.db_name  # hearing/result.json の database.name を使用（未指定時は "${var.project_name}-db"）
  db_name                     = replace(var.project_name, "-", "")
  db_workload                 = "OLTP"
  cpu_core_count              = local.atp_sizing[var.db_sizing].cpu_core_count
  data_storage_size_in_tbs    = local.atp_sizing[var.db_sizing].data_storage_size_in_tbs
  admin_password              = local.atp_admin_password
  is_auto_scaling_enabled     = true

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
```

## MySQL Database Service — 動的生成パターン

```hcl
variable "mysql_admin_username" {
  description = "Admin username for MySQL Database Service"
  type        = string
  default     = "mysqladmin"
}

variable "mysql_admin_password" {
  description = "Admin password for MySQL Database Service"
  type        = string
  sensitive   = true
}

locals {
  # sizing マッピング
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
  display_name        = var.db_name  # hearing/result.json の database.name を使用（未指定時は "${var.project_name}-db"）
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
```
