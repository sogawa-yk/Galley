# ============================================================
# URL Token - 自動生成される認証トークン
# ============================================================

resource "random_password" "url_token" {
  length  = 32
  special = false
}

# ============================================================
# API Gateway - HTTPS終端
# ============================================================

resource "oci_apigateway_gateway" "galley" {
  compartment_id             = var.compartment_ocid
  display_name               = "${local.name_prefix}-apigw"
  endpoint_type              = "PUBLIC"
  subnet_id                  = oci_core_subnet.public.id
  network_security_group_ids = [oci_core_network_security_group.public.id]
}

# ============================================================
# API Gateway Deployment - MCPエンドポイントのルーティング
# ============================================================
#
# URLトークン認証の仕組み:
# 1. API Gatewayはクエリパラメータ "token" の存在をログに記録する（PERMISSIVE）
# 2. トークン値の一致検証はGalleyアプリケーション側で実施する
# 3. これにより、OCI Functions等の追加サービスを不要にしている
#
# 注意: validation_modeをENFORCINGにすると、Claude Desktop等のMCPクライアントが
# 初期ハンドシェイク時にtokenなしリクエストを送信した際に400エラーで拒否される。
# そのためPERMISSIVE（ログのみ）に設定し、実際のtoken検証はアプリ側で行う。
#

resource "oci_apigateway_deployment" "galley" {
  compartment_id = var.compartment_ocid
  gateway_id     = oci_apigateway_gateway.galley.id
  display_name   = "${local.name_prefix}-deployment"
  path_prefix    = "/"
  specification {
    routes {
      path    = "/{path*}"
      methods = ["ANY"]

      backend {
        type = "HTTP_BACKEND"
        url  = "http://${oci_container_instances_container_instance.galley.vnics[0].private_ip}:8000/$${request.path[path]}"

        connect_timeout_in_seconds = 10
        read_timeout_in_seconds    = 300
        send_timeout_in_seconds    = 300
      }

      request_policies {
        query_parameter_validations {
          parameters {
            name     = "token"
            required = true
          }

          validation_mode = "PERMISSIVE"
        }
      }
    }
  }
}
