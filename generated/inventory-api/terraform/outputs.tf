# =============================================================================
# Common Outputs
# =============================================================================

output "project_name" {
  value       = var.project_name
  description = "Project name"
}

output "compartment_id" {
  value       = var.compartment_id
  description = "Compartment OCID"
}

# =============================================================================
# Network Outputs
# =============================================================================

output "vcn_id" {
  value       = module.vcn.vcn_id
  description = "VCN OCID"
}

output "public_subnet_id" {
  value       = oci_core_subnet.public_subnet.id
  description = "Public subnet OCID"
}

output "private_subnet_id" {
  value       = oci_core_subnet.private_subnet.id
  description = "Private subnet OCID"
}

# =============================================================================
# Compute Outputs
# =============================================================================

output "compute_instance_id" {
  value       = oci_core_instance.app.id
  description = "Compute instance OCID"
}

output "compute_public_ip" {
  value       = oci_core_instance.app.public_ip
  description = "Compute instance public IP"
}

output "compute_private_ip" {
  value       = oci_core_instance.app.private_ip
  description = "Compute instance private IP"
}

# =============================================================================
# Database Outputs
# =============================================================================

output "db_connection_string" {
  value       = oci_database_autonomous_database.atp.connection_strings[0].all_connection_strings["LOW"]
  description = "ATP database connection string (LOW profile)"
  sensitive   = true
}

output "db_ocid" {
  value       = oci_database_autonomous_database.atp.id
  description = "ATP database OCID"
}

# =============================================================================
# OCIR Output
# =============================================================================

locals {
  ocir_repo_url = "${var.region_key}.ocir.io/${var.tenancy_namespace}/${var.project_name}"
}

output "ocir_repo_url" {
  value       = local.ocir_repo_url
  description = "OCIR repository URL"
}
