# ----- Common Outputs -----

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

# ----- Functions Outputs -----

output "functions_app_id" {
  value       = oci_functions_application.app.id
  description = "Functions Application OCID"
}

# ----- Object Storage Outputs -----

output "object_storage_bucket" {
  value       = oci_objectstorage_bucket.images.name
  description = "Object Storage bucket name for images"
}

output "object_storage_namespace" {
  value       = var.tenancy_namespace
  description = "Object Storage namespace"
}

# ----- API Gateway Outputs -----

output "api_gateway_id" {
  value       = oci_apigateway_gateway.gw.id
  description = "API Gateway OCID"
}

output "api_gateway_hostname" {
  value       = oci_apigateway_gateway.gw.hostname
  description = "API Gateway hostname for public access"
}

output "api_gateway_deployment_id" {
  value       = oci_apigateway_deployment.api.id
  description = "API Gateway Deployment OCID"
}

# ----- OCIR Output -----

output "ocir_repo_url" {
  value       = "${var.region_key}.ocir.io/${var.tenancy_namespace}/${var.project_name}"
  description = "OCIR repository URL"
}
