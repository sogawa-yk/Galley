# =============================================================================
# OKE Cluster — Using official terraform-oci-oke module
# =============================================================================

module "oke" {
  source  = "oracle-terraform-modules/oke/oci"
  version = ">= 5.0.0"

  compartment_id = var.compartment_id
  region         = var.region

  cluster_name       = "${var.project_name}-oke"
  vcn_id             = module.vcn.vcn_id
  kubernetes_version = var.kubernetes_version

  # Node Pool
  node_pools = {
    np1 = {
      shape            = var.compute_shape
      ocpus            = var.compute_ocpu
      memory           = var.compute_memory_gb
      size             = var.node_count
      boot_volume_size = 50
      subnet_id        = oci_core_subnet.private_subnet.id
    }
  }

  # API Endpoint
  control_plane_is_public = true
  api_endpoint_subnet_id  = oci_core_subnet.public_subnet.id

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
