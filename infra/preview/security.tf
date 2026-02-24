# ============================================================
# NSG (Network Security Groups) - 既存dev VCN内のセキュリティ制御
# ============================================================

# パブリックサブネットのCIDR取得（プライベートNSGのingress sourceに使用）
data "oci_core_subnet" "public" {
  subnet_id = var.public_subnet_id
}

# ------------------------------------------------------------
# パブリックNSG - API Gateway用
# ------------------------------------------------------------

resource "oci_core_network_security_group" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_id
  display_name   = "${local.name_prefix}-public-nsg"
}

# Ingress: HTTPS from anywhere
resource "oci_core_network_security_group_security_rule" "public_ingress_https" {
  network_security_group_id = oci_core_network_security_group.public.id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = "0.0.0.0/0"
  source_type               = "CIDR_BLOCK"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

# Egress: All to anywhere
resource "oci_core_network_security_group_security_rule" "public_egress_all" {
  network_security_group_id = oci_core_network_security_group.public.id
  direction                 = "EGRESS"
  protocol                  = "all"
  destination               = "0.0.0.0/0"
  destination_type          = "CIDR_BLOCK"
  stateless                 = false
}

# ------------------------------------------------------------
# プライベートNSG - Container Instance用
# ------------------------------------------------------------

resource "oci_core_network_security_group" "private" {
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_id
  display_name   = "${local.name_prefix}-private-nsg"
}

# Ingress: MCP port from public subnet (API Gateway)
resource "oci_core_network_security_group_security_rule" "private_ingress_mcp" {
  network_security_group_id = oci_core_network_security_group.private.id
  direction                 = "INGRESS"
  protocol                  = "6" # TCP
  source                    = data.oci_core_subnet.public.cidr_block
  source_type               = "CIDR_BLOCK"
  stateless                 = false

  tcp_options {
    destination_port_range {
      min = 8000
      max = 8000
    }
  }
}

# Egress: All to anywhere (Terraform, OCI CLI, kubectl等の外部通信)
resource "oci_core_network_security_group_security_rule" "private_egress_all" {
  network_security_group_id = oci_core_network_security_group.private.id
  direction                 = "EGRESS"
  protocol                  = "all"
  destination               = "0.0.0.0/0"
  destination_type          = "CIDR_BLOCK"
  stateless                 = false
}
