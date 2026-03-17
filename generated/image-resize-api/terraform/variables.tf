# ----- Common Variables -----

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
  default     = "image-resize-api"
}

# ----- OCIR Variables -----

variable "region_key" {
  description = "OCI region key (e.g., nrt, iad)"
  type        = string
}

variable "tenancy_namespace" {
  description = "Tenancy object storage namespace"
  type        = string
}
