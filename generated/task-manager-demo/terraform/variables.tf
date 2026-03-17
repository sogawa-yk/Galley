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
}

# =============================================================================
# Compute (OKE) Variables
# =============================================================================

variable "compute_shape" {
  description = "Shape for OKE node pool instances"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "compute_ocpu" {
  description = "Number of OCPUs for OKE node pool instances"
  type        = number
  default     = 2
}

variable "compute_memory_gb" {
  description = "Memory in GB for OKE node pool instances"
  type        = number
  default     = 16
}

variable "kubernetes_version" {
  description = "Kubernetes version for OKE cluster"
  type        = string
  default     = "v1.28.2"
}

variable "node_count" {
  description = "Number of nodes in OKE node pool"
  type        = number
  default     = 2
}

# =============================================================================
# Database (MySQL) Variables
# =============================================================================

variable "db_sizing" {
  description = "Database sizing tier (minimal, standard, large)"
  type        = string
  default     = "standard"
}

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

# =============================================================================
# OCIR Variables
# =============================================================================

variable "region_key" {
  description = "OCI region key for OCIR (e.g., nrt for ap-tokyo-1)"
  type        = string
  default     = "PLACEHOLDER"
}

variable "tenancy_namespace" {
  description = "Tenancy namespace for OCIR"
  type        = string
  default     = "PLACEHOLDER"
}
