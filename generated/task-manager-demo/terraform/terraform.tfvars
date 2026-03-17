# =============================================================================
# Common
# =============================================================================
compartment_id = "PLACEHOLDER"
region         = "PLACEHOLDER"
project_name   = "task-manager-demo"

# =============================================================================
# Compute (OKE)
# =============================================================================
compute_shape      = "VM.Standard.E4.Flex"
compute_ocpu       = 2
compute_memory_gb  = 16
kubernetes_version = "v1.28.2"
node_count         = 2

# =============================================================================
# Database (MySQL)
# =============================================================================
db_sizing            = "standard"
mysql_admin_username = "mysqladmin"
mysql_admin_password = "PLACEHOLDER"

# =============================================================================
# OCIR
# =============================================================================
region_key        = "PLACEHOLDER"
tenancy_namespace = "PLACEHOLDER"
