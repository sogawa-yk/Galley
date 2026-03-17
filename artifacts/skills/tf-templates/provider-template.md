# Provider Template

## provider.tf パターン

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

provider "oci" {
  region = var.region
}
```

**注意**:
- `backend` ブロックは含めない（Resource Managerがstate管理）
- 認証設定は不要（インスタンスプリンシパル / Resource Managerが自動設定）
