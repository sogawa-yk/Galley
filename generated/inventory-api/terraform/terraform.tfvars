# =============================================================================
# Common
# =============================================================================
compartment_id    = "PLACEHOLDER"
region            = "PLACEHOLDER"
project_name      = "inventory-api"

# =============================================================================
# Compute
# =============================================================================
compute_shape     = "VM.Standard.E4.Flex"
compute_ocpu      = 1
compute_memory_gb = 8
compute_image_id  = "PLACEHOLDER"  # Oracle Linux image OCID

# =============================================================================
# Database
# =============================================================================
db_sizing = "minimal"
db_name   = "inventory-db"

# =============================================================================
# OCIR
# =============================================================================
region_key        = "PLACEHOLDER"  # e.g., nrt, iad, phx
tenancy_namespace = "PLACEHOLDER"  # tenancy object storage namespace
