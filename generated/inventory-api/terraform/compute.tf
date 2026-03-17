# =============================================================================
# Availability Domains
# =============================================================================

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

# =============================================================================
# Compute Instance
# =============================================================================

resource "oci_core_instance" "app" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "${var.project_name}-vm"
  shape               = var.compute_shape

  shape_config {
    ocpus         = var.compute_ocpu
    memory_in_gbs = var.compute_memory_gb
  }

  source_details {
    source_type = "image"
    source_id   = var.compute_image_id
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public_subnet.id
    assign_public_ip = true
    display_name     = "${var.project_name}-vnic"
  }

  metadata = {
    user_data = base64encode(file("${path.module}/cloud-init.sh"))
  }

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
