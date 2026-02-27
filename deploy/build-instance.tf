# ============================================================
# Build Instance - Docker イメージビルド用 Compute Instance
# ============================================================

# Oracle Linux 8 の最新プラットフォームイメージを取得
data "oci_core_images" "oracle_linux_8" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.build_instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "build" {
  compartment_id      = var.compartment_ocid
  availability_domain = local.availability_domain
  display_name        = "${local.name_prefix}-build"
  shape               = var.build_instance_shape

  shape_config {
    ocpus         = var.build_instance_ocpus
    memory_in_gbs = var.build_instance_memory_in_gbs
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux_8.images[0].id
  }

  create_vnic_details {
    subnet_id              = oci_core_subnet.private.id
    display_name           = "${local.name_prefix}-build-vnic"
    assign_public_ip       = false
    nsg_ids                = [oci_core_network_security_group.private.id]
  }

  metadata = {
    user_data = base64encode(local.build_cloud_init)
  }

  # Instance Agent Run Command プラグインを有効化
  agent_config {
    plugins_config {
      name          = "Run Command"
      desired_state = "ENABLED"
    }
    plugins_config {
      name          = "Bastion"
      desired_state = "DISABLED"
    }
  }
}

locals {
  build_cloud_init = <<-EOF
    #!/bin/bash
    set -e

    # OCI CLI インストール (Instance Principal でのObject Storage/OCIR認証に必要)
    dnf -y install python39-oci-cli || pip3 install oci-cli

    # Docker Engine インストール (Oracle Linux 8)
    dnf -y install docker-engine docker-cli
    systemctl enable --now docker

    # ビルド用作業ディレクトリ
    mkdir -p /opt/galley-build
    chmod 755 /opt/galley-build

    # 準備完了マーカー
    touch /opt/galley-build/.ready
  EOF
}
