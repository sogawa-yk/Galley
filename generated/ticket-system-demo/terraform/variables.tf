# --- Common Variables ---

variable "compartment_id" {
  description = "Compartment OCID"
  type        = string
}

variable "region" {
  description = "OCI region"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ticket-system-demo"
}

# --- Container Instances Variables ---

variable "ci_ocpus" {
  description = "OCPU count for Container Instance"
  type        = number
  default     = 1
}

variable "ci_memory_gb" {
  description = "Memory in GB for Container Instance"
  type        = number
  default     = 8
}

# --- Database Variables ---

variable "db_sizing" {
  description = "Database sizing tier (minimal/standard/large)"
  type        = string
  default     = "minimal"
}

variable "db_name" {
  description = "Database display name"
  type        = string
  default     = "ticket-system-demo-db"
}

variable "mysql_admin_username" {
  description = "Admin username for MySQL Database Service"
  type        = string
  default     = "mysqladmin"
}

variable "mysql_admin_password" {
  description = "Admin password for MySQL Database Service. If not set, a random password is generated."
  type        = string
  sensitive   = true
  default     = null
}

# --- OCIR Variables ---

variable "region_key" {
  description = "OCI region key for OCIR (e.g., nrt for Tokyo)"
  type        = string
}

variable "tenancy_namespace" {
  description = "Tenancy object storage namespace for OCIR"
  type        = string
}
