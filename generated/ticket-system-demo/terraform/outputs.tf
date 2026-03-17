# --- Common Outputs ---

output "project_name" {
  value       = var.project_name
  description = "Project name"
}

output "compartment_id" {
  value       = var.compartment_id
  description = "Compartment OCID"
}

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

# --- Container Instances Outputs ---

output "container_instance_subnet_id" {
  value       = oci_core_subnet.private_subnet.id
  description = "Subnet OCID for container instance deployment"
}

# --- Database Outputs ---

output "db_connection_string" {
  value       = oci_mysql_mysql_db_system.mysql.endpoints[0].hostname
  description = "MySQL Database connection hostname"
  sensitive   = true
}

output "db_ocid" {
  value       = oci_mysql_mysql_db_system.mysql.id
  description = "MySQL Database System OCID"
}

# --- Load Balancer Outputs ---

output "lb_public_ip" {
  value       = oci_load_balancer_load_balancer.lb.ip_addresses[0].ip_address
  description = "Load Balancer public IP"
}

output "lb_ocid" {
  value       = oci_load_balancer_load_balancer.lb.id
  description = "Load Balancer OCID"
}

# --- OCIR Output ---

output "ocir_repo_url" {
  value       = "${var.region_key}.ocir.io/${var.tenancy_namespace}/${var.project_name}"
  description = "OCIR repository URL"
}
