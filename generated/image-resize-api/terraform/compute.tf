# ----- Functions Application -----

resource "oci_functions_application" "app" {
  compartment_id = var.compartment_id
  display_name   = "${var.project_name}-fn-app"
  subnet_ids     = [oci_core_subnet.private_subnet.id]

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

# Note: Individual function definitions are managed by deploy-app skill.
# Functions are deployed via `fn deploy` CLI which creates
# oci_functions_function resources automatically.
