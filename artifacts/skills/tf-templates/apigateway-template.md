# API Gateway Template

## API Gateway — 動的生成パターン

Functions をバックエンドとする API Gateway の構成例。パブリックサブネットに配置し、Functions への HTTP ルーティングを提供する。

### Gateway リソース

```hcl
resource "oci_apigateway_gateway" "gateway" {
  compartment_id = var.compartment_id
  display_name   = "${var.project_name}-apigw"
  endpoint_type  = "PUBLIC"
  subnet_id      = oci_core_subnet.public_subnet.id

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
```

### Deployment リソース（Functions バックエンド）

```hcl
resource "oci_apigateway_deployment" "deployment" {
  compartment_id = var.compartment_id
  gateway_id     = oci_apigateway_gateway.gateway.id
  display_name   = "${var.project_name}-apigw-deployment"
  path_prefix    = "/"

  specification {
    # ヘルスチェック用ルート（verify スキルが使用）
    routes {
      path    = "/health"
      methods = ["GET"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = oci_functions_function.fn.id
      }
    }

    # メインAPIルート — アプリケーションのルーティングに合わせてパスを調整
    routes {
      path    = "/{path*}"
      methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = oci_functions_function.fn.id
      }
    }
  }

  freeform_tags = {
    "project"    = var.project_name
    "managed_by" = "oci-demo-builder"
    "created_by" = "terraform"
  }
}
```

### 出力

```hcl
output "api_gateway_url" {
  value       = oci_apigateway_deployment.deployment.endpoint
  description = "API Gateway deployment endpoint URL"
}
```

### 注意事項

- Gateway は `endpoint_type = "PUBLIC"` でパブリックサブネットに配置
- Deployment の `path_prefix` は `"/"` を使用し、個別ルートで各パスを定義
- `/health` ルートを必ず含めること（verify スキルのヘルスチェックが依存）
- `/{path*}` ワイルドカードルートで残りのリクエストを Functions に転送
- `function_id` は `oci_functions_function.fn.id` を参照（compute-templates.md の Functions セクション参照）
