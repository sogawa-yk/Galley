# =============================================================================
# Load Balancer
# =============================================================================

resource "oci_load_balancer_load_balancer" "lb" {
  compartment_id = var.compartment_id
  display_name   = "${var.project_name}-lb"
  shape          = "flexible"

  shape_details {
    minimum_bandwidth_in_mbps = 10
    maximum_bandwidth_in_mbps = 100
  }

  subnet_ids = [oci_core_subnet.public_subnet.id]

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

# =============================================================================
# Backend Set
# =============================================================================

resource "oci_load_balancer_backend_set" "app_backend_set" {
  load_balancer_id = oci_load_balancer_load_balancer.lb.id
  name             = "${var.project_name}-backend-set"
  policy           = "ROUND_ROBIN"

  health_checker {
    protocol          = "HTTP"
    url_path          = "/health"
    port              = 8080
    interval_ms       = 10000
    timeout_in_millis = 3000
    retries           = 3
  }

  # Backends are configured by deploy-app after deployment
}

# =============================================================================
# Listener
# =============================================================================

resource "oci_load_balancer_listener" "http_listener" {
  load_balancer_id         = oci_load_balancer_load_balancer.lb.id
  name                     = "${var.project_name}-http-listener"
  port                     = 80
  protocol                 = "HTTP"
  default_backend_set_name = oci_load_balancer_backend_set.app_backend_set.name
}
