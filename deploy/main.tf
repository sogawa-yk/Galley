terraform {
  required_version = ">= 1.5.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0"
    }
  }
}

provider "oci" {
  region = var.region
}

provider "random" {}

# Object Storageネームスペースの取得
data "oci_objectstorage_namespace" "current" {
  compartment_id = var.compartment_ocid
}

# 利用可能なAvailability Domainの取得
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

locals {
  # 作業対象コンパートメント（未指定時はcompartment_idと同じ）
  work_compartment_id = coalesce(var.galley_work_compartment_id, var.compartment_ocid)

  # 最初のAvailability Domain
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name

  # リソース名のプレフィックス
  name_prefix = "galley"

}
