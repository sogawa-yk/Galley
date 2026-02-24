# ============================================================
# Container Instance - Galley MCPサーバーの実行環境
# ============================================================

locals {
  # コンテナイメージURL（未指定時はデフォルトのOCIRリポジトリ）
  container_image_url = var.galley_image_url != "" ? var.galley_image_url : "${var.region}.ocir.io/${data.oci_objectstorage_namespace.current.namespace}/galley:${var.image_tag}"
}

resource "oci_container_instances_container_instance" "galley" {
  compartment_id       = var.compartment_ocid
  availability_domain  = local.availability_domain
  display_name         = "${local.name_prefix}-server"
  graceful_shutdown_timeout_in_seconds = 30

  shape = var.container_instance_shape
  shape_config {
    ocpus         = var.container_instance_ocpus
    memory_in_gbs = var.container_instance_memory_in_gbs
  }

  vnics {
    subnet_id              = var.private_subnet_id
    display_name           = "${local.name_prefix}-vnic"
    is_public_ip_assigned  = false
    nsg_ids                = [oci_core_network_security_group.private.id]
  }

  containers {
    display_name = "${local.name_prefix}-mcp"
    image_url    = local.container_image_url

    environment_variables = {
      "GALLEY_HOST"             = "0.0.0.0"
      "GALLEY_PORT"             = "8000"
      "GALLEY_DATA_DIR"         = "/data"
      "GALLEY_CONFIG_DIR"       = "/app/config"
      "GALLEY_BUCKET_NAME"      = oci_objectstorage_bucket.galley.name
      "GALLEY_BUCKET_NAMESPACE" = data.oci_objectstorage_namespace.current.namespace
      "GALLEY_REGION"           = var.region
      "GALLEY_URL_TOKEN"        = random_password.url_token.result
    }

    health_checks {
      health_check_type = "HTTP"
      port              = 8000
      path              = "/health"
      interval_in_seconds          = 30
      timeout_in_seconds           = 5
      success_threshold            = 1
      failure_threshold            = 3
      initial_delay_in_seconds     = 10
    }

    resource_config {
      vcpus_limit        = var.container_instance_ocpus
      memory_limit_in_gbs = var.container_instance_memory_in_gbs
    }
  }
}
