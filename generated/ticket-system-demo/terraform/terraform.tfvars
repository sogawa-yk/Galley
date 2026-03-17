# --- Required: Set these before running terraform plan ---
compartment_id = "PLACEHOLDER"
region         = "PLACEHOLDER"
region_key     = "PLACEHOLDER"
tenancy_namespace = "PLACEHOLDER"

# --- Project ---
project_name = "ticket-system-demo"

# --- Container Instances ---
ci_ocpus     = 1
ci_memory_gb = 8

# --- Database ---
db_sizing          = "minimal"
db_name            = "ticket-system-demo-db"
mysql_admin_username = "mysqladmin"
# mysql_admin_password is generated randomly if not set
