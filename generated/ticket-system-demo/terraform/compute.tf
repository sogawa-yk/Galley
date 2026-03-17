# --- Availability Domains ---

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

# --- Container Instance ---

resource "oci_container_instances_container_instance" "app" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "${var.project_name}-ci"

  container_restart_policy = "ALWAYS"

  shape = "CI.Standard.E4.Flex"
  shape_config {
    ocpus         = var.ci_ocpus
    memory_in_gbs = var.ci_memory_gb
  }

  # Private subnet (behind load balancer)
  vnics {
    subnet_id = oci_core_subnet.private_subnet.id
  }

  containers {
    display_name = "${var.project_name}-app"
    image_url    = "PLACEHOLDER_IMAGE_URL" # deploy-app が後から設定
  }

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
