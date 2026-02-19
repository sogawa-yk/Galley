output "mcp_endpoint_url" {
  description = "MCP接続用エンドポイントURL（URLトークン付き）。MCPホスト（Claude Desktop等）の設定に使用。"
  value       = "${oci_apigateway_gateway.galley.hostname}/mcp?token=${nonsensitive(random_password.url_token.result)}"
}

output "api_gateway_hostname" {
  description = "API Gatewayのホスト名"
  value       = oci_apigateway_gateway.galley.hostname
}

output "url_token" {
  description = "URLトークン（認証用）"
  value       = nonsensitive(random_password.url_token.result)
}

output "object_storage_bucket" {
  description = "Galley用Object Storageバケット名"
  value       = oci_objectstorage_bucket.galley.name
}

output "object_storage_namespace" {
  description = "Object Storageネームスペース"
  value       = data.oci_objectstorage_namespace.current.namespace
}

output "container_instance_id" {
  description = "Container InstanceのOCID"
  value       = oci_container_instances_container_instance.galley.id
}

output "container_instance_private_ip" {
  description = "Container InstanceのプライベートIPアドレス"
  value       = oci_container_instances_container_instance.galley.vnics[0].private_ip
}

output "vcn_id" {
  description = "VCNのOCID"
  value       = oci_core_vcn.galley.id
}
