# Compute Templates

## OKE — 公式モジュール使用パターン

```hcl
module "oke" {
  source  = "oracle-terraform-modules/oke/oci"
  version = ">= 5.0.0"

  compartment_id = var.compartment_id
  region         = var.region

  cluster_name    = "${var.project_name}-oke"
  vcn_id          = module.vcn.vcn_id
  kubernetes_version = "v1.28.2"

  # Node Pool
  node_pools = {
    np1 = {
      shape            = var.node_shape
      ocpus            = var.node_ocpus
      memory           = var.node_memory_gb
      size             = var.node_count
      boot_volume_size = 50
      subnet_id        = oci_core_subnet.private_subnet.id
    }
  }

  # API Endpoint
  control_plane_is_public = true
  api_endpoint_subnet_id  = oci_core_subnet.public_subnet.id

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
```

## Container Instances — 動的生成パターン

```hcl
resource "oci_container_instances_container_instance" "app" {
  compartment_id          = var.compartment_id
  availability_domain     = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name            = "${var.project_name}-ci"
  container_restart_policy = "ALWAYS"

  shape = "CI.Standard.E4.Flex"
  shape_config {
    ocpus         = var.ci_ocpus
    memory_in_gbs = var.ci_memory_gb
  }

  vnics {
    subnet_id = oci_core_subnet.public_subnet.id
  }

  containers {
    display_name = "${var.project_name}-app"
    image_url    = "PLACEHOLDER_IMAGE_URL"  # deploy-app が後から設定
  }

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}
```

## Compute Instance — 動的生成パターン

```hcl
resource "oci_core_instance" "app" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "${var.project_name}-vm"
  shape               = var.compute_shape

  shape_config {
    ocpus         = var.compute_ocpu
    memory_in_gbs = var.compute_memory_gb
  }

  source_details {
    source_type = "image"
    source_id   = var.compute_image_id  # Oracle Linux
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public_subnet.id
    assign_public_ip = true
  }

  metadata = {
    user_data = base64encode(file("${path.module}/cloud-init.sh"))
  }

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
```

## Functions — 動的生成パターン

Functions では Application（関数のコンテナ）と Function（個別の関数定義）の両方が必要です。

```hcl
resource "oci_functions_application" "app" {
  compartment_id = var.compartment_id
  display_name   = "${var.project_name}-fn-app"
  subnet_ids     = [oci_core_subnet.private_subnet.id]

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}

resource "oci_functions_function" "fn" {
  application_id = oci_functions_application.app.id
  display_name   = var.project_name
  memory_in_mbs  = var.function_memory_mb  # sizing.memory_mb から（デフォルト: 256）
  timeout_in_seconds = var.function_timeout_sec  # sizing.timeout_sec から（デフォルト: 120）

  # イメージURLは fn deploy 後に自動設定されるため、初期値はプレースホルダー
  image = "PLACEHOLDER_IMAGE_URL"

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
```

**注意**:
- `oci_functions_application` だけでは不十分。`oci_functions_function` も必ず定義すること
- `image` フィールドはプレースホルダー。`fn deploy` が実行時に正しいOCIRイメージURLに更新する
- API Gateway を使用する場合は `oci_functions_function.fn.id` を API Gateway の backend で参照する（apigateway-template.md 参照）
