# Hearing Result Schema

hearing/result.json の構造定義です。hearing.md Skill がこのスキーマに従って結果を出力します。

## 必須フィールド

以下のフィールドは必ず含めてください:

| Field | Type | Description | Example |
|---|---|---|---|
| `project_name` | string | プロジェクト名（英数字+ハイフン、先頭英字、最大32文字） | `"ecommerce-demo"` |
| `app_type` | string | アプリケーション種別 | `"web"`, `"api"`, `"batch"`, `"serverless"`, `"microservices"` |
| `compute_type` | string | コンピュート種別 | `"oke"`, `"container_instances"`, `"compute"`, `"functions"` |
| `compute_new_or_existing` | string | 新規作成 or 既存利用 | `"new"`, `"existing"` |
| `language` | string | プログラミング言語 | `"python"`, `"java"`, `"nodejs"`, `"go"` |
| `framework` | string | フレームワーク | `"fastapi"`, `"spring-boot"`, `"express"`, `"gin"` |
| `container` | string | コンテナ化方式 | `"docker"`, `"none"`, `"functions"` |
| `purpose` | string | デモ環境の目的 | `"customer_demo"`, `"poc"`, `"training"`, `"performance_test"` |

## 動的フィールド

要望に応じて以下のフィールドを追加してください:

### database (データベース関連)
```json
{
  "database": {
    "type": "atp|mysql|nosql|none",
    "sizing": "minimal|standard|large",
    "name": "string (DB表示名。未指定時は {project_name}-db を使用)"
  }
}
```

### network (ネットワーク関連)
```json
{
  "network": {
    "vcn": "new|existing",
    "vcn_id": "string (existing の場合)",
    "subnet_type": "public|private",
    "load_balancer": true|false,
    "access_type": "public|private|lb_public"
  }
}
```

### sizing (サイジング)
```json
{
  "sizing": {
    "ocpu": 1,
    "memory_gb": 8,
    "shape": "VM.Standard.E4.Flex"
  }
}
```

### additional_services (追加サービス)
```json
{
  "additional_services": ["object_storage", "streaming", "api_gateway", "logging"]
}
```

### sample_data (サンプルデータ)
```json
{
  "sample_data": {
    "description": "string",
    "seed_required": true|false
  }
}
```

### custom_requirements (カスタム要件)
```json
{
  "custom_requirements": ["string"]
}
```

### warnings (残存矛盾)
```json
{
  "warnings": ["矛盾の説明テキスト"]
}
```

## 完全なサンプル

```json
{
  "project_name": "ecommerce-demo",
  "app_type": "web",
  "compute_type": "container_instances",
  "compute_new_or_existing": "new",
  "language": "python",
  "framework": "fastapi",
  "container": "docker",
  "purpose": "customer_demo",
  "database": {
    "type": "atp",
    "sizing": "minimal",
    "name": "ecommerce-db"
  },
  "network": {
    "vcn": "new",
    "subnet_type": "public",
    "load_balancer": true,
    "access_type": "lb_public"
  },
  "sizing": {
    "ocpu": 1,
    "memory_gb": 8,
    "shape": "VM.Standard.E4.Flex"
  },
  "additional_services": ["object_storage"],
  "sample_data": {
    "description": "商品カタログと注文履歴のサンプルデータ",
    "seed_required": true
  },
  "warnings": []
}
```

## project_name 命名規則

- 英数字とハイフンのみ使用可（`[a-z0-9-]+`）
- 先頭は英字（`[a-z]`で始まる）
- 最大32文字
- ユーザーが指定しない場合: 要望内容から英語スラッグを自動生成
- 例: 「Eコマースのデモ」→ `ecommerce-demo`、「APIサーバー検証」→ `api-server-test`
