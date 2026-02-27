variable "tenancy_ocid" {
  description = "テナンシーOCID（Resource Managerが自動注入）"
  type        = string
}

variable "compartment_ocid" {
  description = "Galleyインフラを配置するコンパートメントOCID"
  type        = string

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid)) || can(regex("^ocid1\\.tenancy\\.", var.compartment_ocid))
    error_message = "compartment_ocid はコンパートメントまたはテナンシーのOCIDである必要があります。"
  }
}

variable "region" {
  description = "OCIリージョン（例: ap-tokyo-1）"
  type        = string
}

variable "galley_work_compartment_id" {
  description = "Galleyの作業対象コンパートメントOCID。未指定時はcompartment_idと同じ。"
  type        = string
  default     = null

  validation {
    condition     = var.galley_work_compartment_id == null || can(regex("^ocid1\\.(compartment|tenancy)\\.", var.galley_work_compartment_id))
    error_message = "galley_work_compartment_id はコンパートメントまたはテナンシーのOCIDである必要があります。"
  }
}

variable "vcn_cidr" {
  description = "VCNのCIDRブロック"
  type        = string
  default     = "10.0.0.0/16"
}

variable "galley_image_url" {
  description = "GalleyコンテナイメージのフルURL"
  type        = string
  default     = "ghcr.io/sogawa-yk/galley:latest"
}

variable "container_instance_shape" {
  description = "Container Instanceのシェイプ"
  type        = string
  default     = "CI.Standard.E4.Flex"
}

variable "container_instance_ocpus" {
  description = "Container Instanceに割り当てるOCPU数"
  type        = number
  default     = 1
}

variable "container_instance_memory_in_gbs" {
  description = "Container Instanceに割り当てるメモリ（GB）"
  type        = number
  default     = 2
}

# ============================================================
# Build Instance
# ============================================================

variable "build_instance_shape" {
  description = "Build Instanceのシェイプ"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "build_instance_ocpus" {
  description = "Build Instanceに割り当てるOCPU数"
  type        = number
  default     = 1
}

variable "build_instance_memory_in_gbs" {
  description = "Build Instanceに割り当てるメモリ（GB）"
  type        = number
  default     = 8
}

# ============================================================
# OCIR (Container Registry) 認証
# ============================================================

variable "ocir_username" {
  description = "OCIR認証ユーザー名（例: namespace/oracleidentitycloudservice/user@example.com）"
  type        = string
  default     = ""
}

variable "ocir_auth_token" {
  description = "OCIR認証トークン（OCI Console → User Settings → Auth Tokens で生成）"
  type        = string
  sensitive   = true
  default     = ""
}
