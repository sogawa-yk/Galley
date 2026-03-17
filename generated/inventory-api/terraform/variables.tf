# =============================================================================
# Common Variables
# =============================================================================

variable "compartment_id" {
  description = "Compartment OCID"
  type        = string
}

variable "region" {
  description = "OCI Region"
  type        = string
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "inventory-api"
}

# =============================================================================
# Compute Variables
# =============================================================================

variable "compute_shape" {
  description = "Compute instance shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "compute_ocpu" {
  description = "Number of OCPUs for the compute instance"
  type        = number
  default     = 1
}

variable "compute_memory_gb" {
  description = "Memory in GB for the compute instance"
  type        = number
  default     = 8
}

variable "compute_image_id" {
  description = "OCID of the Oracle Linux image for the compute instance"
  type        = string
}

# =============================================================================
# Database Variables
# =============================================================================

variable "db_sizing" {
  description = "Database sizing tier (minimal, standard, large)"
  type        = string
  default     = "minimal"
}

variable "db_name" {
  description = "Display name for the database"
  type        = string
  default     = "inventory-db"
}

variable "atp_admin_password" {
  description = "Admin password for ATP. If not set, a random password is generated."
  type        = string
  sensitive   = true
  default     = null
}

# =============================================================================
# OCIR Variables
# =============================================================================

variable "region_key" {
  description = "OCI region key for OCIR (e.g., nrt for ap-tokyo-1)"
  type        = string
}

variable "tenancy_namespace" {
  description = "Tenancy object storage namespace for OCIR"
  type        = string
}
