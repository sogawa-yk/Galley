# =============================================================================
# Logging — Log Group + Custom Log
# =============================================================================

resource "oci_logging_log_group" "log_group" {
  compartment_id = var.compartment_id
  display_name   = "${var.project_name}-log-group"
  description    = "Log group for ${var.project_name}"

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

resource "oci_logging_log" "app_log" {
  display_name = "${var.project_name}-app-log"
  log_group_id = oci_logging_log_group.log_group.id
  log_type     = "CUSTOM"

  configuration {
    source {
      category    = "all"
      resource    = module.oke.cluster_id
      service     = "oke"
      source_type = "OCISERVICE"
    }
  }

  is_enabled         = true
  retention_duration = 30

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
