# =============================================================================
# VCN — Using official terraform-oci-vcn module
# =============================================================================

module "vcn" {
  source  = "oracle-terraform-modules/vcn/oci"
  version = ">= 3.6.0"

  compartment_id = var.compartment_id
  vcn_name       = "${var.project_name}-vcn"
  vcn_dns_label  = replace(var.project_name, "-", "")
  vcn_cidrs      = ["10.0.0.0/16"]

  create_internet_gateway = true
  create_nat_gateway      = true
  create_service_gateway  = true

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

# =============================================================================
# Subnets
# =============================================================================

resource "oci_core_subnet" "public_subnet" {
  compartment_id = var.compartment_id
  vcn_id         = module.vcn.vcn_id
  cidr_block     = "10.0.0.0/24"
  display_name   = "${var.project_name}-public-subnet"
  dns_label      = "pub"
  route_table_id = module.vcn.ig_route_id

  security_list_ids = [oci_core_security_list.public_sl.id]

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

resource "oci_core_subnet" "private_subnet" {
  compartment_id = var.compartment_id
  vcn_id         = module.vcn.vcn_id
  cidr_block     = "10.0.1.0/24"
  display_name   = "${var.project_name}-private-subnet"
  dns_label      = "priv"
  route_table_id = module.vcn.nat_route_id

  prohibit_public_ip_on_vnic = true
  security_list_ids          = [oci_core_security_list.private_sl.id]

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

# =============================================================================
# Security Lists
# =============================================================================

resource "oci_core_security_list" "public_sl" {
  compartment_id = var.compartment_id
  vcn_id         = module.vcn.vcn_id
  display_name   = "${var.project_name}-public-sl"

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

resource "oci_core_security_list" "private_sl" {
  compartment_id = var.compartment_id
  vcn_id         = module.vcn.vcn_id
  display_name   = "${var.project_name}-private-sl"

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "10.0.0.0/16"
    tcp_options {
      min = 3306
      max = 3306
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "10.0.0.0/16"
    tcp_options {
      min = 8080
      max = 8080
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "10.0.0.0/16"
    tcp_options {
      min = 10250
      max = 10250
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "10.0.0.0/16"
    tcp_options {
      min = 6443
      max = 6443
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
