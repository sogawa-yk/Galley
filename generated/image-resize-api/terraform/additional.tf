# ----- Object Storage Bucket -----

resource "oci_objectstorage_bucket" "images" {
  compartment_id = var.compartment_id
  namespace      = var.tenancy_namespace
  name           = "${var.project_name}-images"
  access_type    = "NoPublicAccess"

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

# ----- API Gateway -----

resource "oci_apigateway_gateway" "gw" {
  compartment_id = var.compartment_id
  display_name   = "${var.project_name}-apigw"
  endpoint_type  = "PUBLIC"
  subnet_id      = oci_core_subnet.public_subnet.id

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

resource "oci_apigateway_deployment" "api" {
  compartment_id = var.compartment_id
  gateway_id     = oci_apigateway_gateway.gw.id
  display_name   = "${var.project_name}-api-deployment"
  path_prefix    = "/v1"

  specification {
    routes {
      path    = "/resize"
      methods = ["POST"]
      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = "PLACEHOLDER_FUNCTION_ID" # Set after function deployment
      }
    }
  }

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
