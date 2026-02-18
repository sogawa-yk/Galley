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

variable "image_tag" {
  description = "Galleyコンテナイメージのタグ"
  type        = string
  default     = "latest"
}

variable "galley_image_url" {
  description = "GalleyコンテナイメージのフルURL。未指定時はOCIRリポジトリから自動生成。"
  type        = string
  default     = ""
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
