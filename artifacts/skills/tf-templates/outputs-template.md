# Outputs Template

## outputs.tf パターン

後続ユニット（deploy-app, verify）が `stack_outputs.json` 経由で参照するため、
必要な情報をすべてoutputとして定義する。

### 共通出力（常に含める）

```hcl
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
```

### OKE出力

```hcl
output "oke_cluster_id" {
  value       = module.oke.cluster_id
  description = "OKE cluster OCID"
}

output "oke_kubeconfig" {
  value       = module.oke.kubeconfig
  description = "Kubeconfig for OKE cluster"
  sensitive   = true
}
```

### Container Instances出力

```hcl
output "container_instance_subnet_id" {
  value       = oci_core_subnet.private_subnet.id
  description = "Subnet OCID for container instance deployment"
}
```

### Compute出力

```hcl
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
```

### Functions出力

```hcl
output "functions_app_id" {
  value       = oci_functions_application.app.id
  description = "Functions Application OCID"
}

output "functions_invoke_endpoint" {
  value       = oci_functions_application.app.invoke_endpoint
  description = "Functions invoke base URL"
}
```

### API Gateway出力（additional_servicesにapi_gatewayがある場合）

```hcl
output "api_gateway_url" {
  value       = oci_apigateway_deployment.deployment.endpoint
  description = "API Gateway deployment endpoint URL"
}
```

### Database出力（ATP）

```hcl
output "db_connection_string" {
  value       = oci_database_autonomous_database.atp.connection_strings[0].all_connection_strings["LOW"]
  description = "ATP Database connection string (TNS format)"
  sensitive   = true
}

output "db_ocid" {
  value       = oci_database_autonomous_database.atp.id
  description = "Autonomous Database OCID"
}
```

### Database出力（MySQL）

```hcl
output "db_host" {
  value       = oci_mysql_mysql_db_system.mysql.ip_address
  description = "MySQL Database Service IP address"
}

output "db_port" {
  value       = oci_mysql_mysql_db_system.mysql.port
  description = "MySQL Database Service port"
}

output "db_user" {
  value       = var.mysql_admin_username
  description = "MySQL admin username"
}

output "db_connection_string" {
  value       = "mysql://${var.mysql_admin_username}:${var.mysql_admin_password}@${oci_mysql_mysql_db_system.mysql.ip_address}:${oci_mysql_mysql_db_system.mysql.port}/${replace(var.project_name, "-", "_")}"
  description = "MySQL connection string (URL format)"
  sensitive   = true
}

output "db_ocid" {
  value       = oci_mysql_mysql_db_system.mysql.id
  description = "MySQL DB System OCID"
}
```

### OCIR出力（常に含める）

```hcl
output "ocir_repo_url" {
  value       = "${var.region_key}.ocir.io/${var.tenancy_namespace}/${var.project_name}"
  description = "OCIR repository URL"
}
```

### Load Balancer出力

```hcl
output "lb_public_ip" {
  value       = oci_load_balancer_load_balancer.lb.ip_addresses[0].ip_address
  description = "Load Balancer public IP"
}

output "lb_ocid" {
  value       = oci_load_balancer_load_balancer.lb.id
  description = "Load Balancer OCID"
}
```
