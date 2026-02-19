# ============================================================
# VCN
# ============================================================

resource "oci_core_vcn" "galley" {
  compartment_id = var.compartment_ocid
  display_name   = "${local.name_prefix}-vcn"
  cidr_blocks    = ["10.0.0.0/16"]
  dns_label      = "galley"
}

# ============================================================
# Gateways
# ============================================================

resource "oci_core_internet_gateway" "galley" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-igw"
  enabled        = true
}

resource "oci_core_nat_gateway" "galley" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-natgw"
}

data "oci_core_services" "all" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

resource "oci_core_service_gateway" "galley" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-sgw"
  services {
    service_id = data.oci_core_services.all.services[0].id
  }
}

# ============================================================
# Route Tables
# ============================================================

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-public-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.galley.id
  }
}

resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-private-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.galley.id
  }

  route_rules {
    destination       = data.oci_core_services.all.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.galley.id
  }
}

# ============================================================
# Security Lists
# ============================================================

resource "oci_core_security_list" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-public-sl"
  # HTTPS inbound
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    stateless   = false

    tcp_options {
      min = 443
      max = 443
    }
  }

  # All outbound
  egress_security_rules {
    protocol         = "all"
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    stateless        = false
  }
}

resource "oci_core_security_list" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-private-sl"
  # Galley MCP port from public subnet (API Gateway)
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = oci_core_subnet.public.cidr_block
    source_type = "CIDR_BLOCK"
    stateless   = false

    tcp_options {
      min = 8000
      max = 8000
    }
  }

  # All outbound (Terraform, OCI CLI, kubectl等の外部通信)
  egress_security_rules {
    protocol         = "all"
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    stateless        = false
  }
}

# ============================================================
# Subnets
# ============================================================

resource "oci_core_subnet" "public" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.galley.id
  display_name               = "${local.name_prefix}-public-subnet"
  cidr_block                 = "10.0.1.0/24"
  dns_label                  = "pub"
  prohibit_internet_ingress  = false
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.public.id]
}

resource "oci_core_subnet" "private" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.galley.id
  display_name               = "${local.name_prefix}-private-subnet"
  cidr_block                 = "10.0.2.0/24"
  dns_label                  = "priv"
  prohibit_internet_ingress  = true
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.private.id
  security_list_ids          = [oci_core_security_list.private.id]
}
