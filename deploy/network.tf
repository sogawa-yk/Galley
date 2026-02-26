# ============================================================
# VCN + ネットワークリソース一式
# ============================================================

# OCI Servicesの一覧（Service Gateway用）
data "oci_core_services" "all" {}

locals {
  # "All <region> Services In Oracle Services Network" を取得
  all_services = [for s in data.oci_core_services.all.services : s if can(regex("^All ", s.name))][0]
}

# ------------------------------------------------------------
# VCN
# ------------------------------------------------------------

resource "oci_core_vcn" "galley" {
  compartment_id = var.compartment_ocid
  display_name   = "${local.name_prefix}-vcn"
  cidr_blocks    = [var.vcn_cidr]
  dns_label      = "galley"
}

# ------------------------------------------------------------
# Gateways
# ------------------------------------------------------------

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

resource "oci_core_service_gateway" "galley" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-sgw"

  services {
    service_id = local.all_services.id
  }
}

# ------------------------------------------------------------
# Route Tables
# ------------------------------------------------------------

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-public-rt"

  route_rules {
    network_entity_id = oci_core_internet_gateway.galley.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.galley.id
  display_name   = "${local.name_prefix}-private-rt"

  route_rules {
    network_entity_id = oci_core_nat_gateway.galley.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }

  route_rules {
    network_entity_id = oci_core_service_gateway.galley.id
    destination       = local.all_services.cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
  }
}

# ------------------------------------------------------------
# Subnets
# ------------------------------------------------------------

resource "oci_core_subnet" "public" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.galley.id
  display_name               = "${local.name_prefix}-public-subnet"
  cidr_block                 = cidrsubnet(var.vcn_cidr, 8, 0)
  dns_label                  = "pub"
  prohibit_internet_ingress  = false
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.public.id
}

resource "oci_core_subnet" "private" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.galley.id
  display_name               = "${local.name_prefix}-private-subnet"
  cidr_block                 = cidrsubnet(var.vcn_cidr, 8, 1)
  dns_label                  = "priv"
  prohibit_internet_ingress  = true
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.private.id
}
