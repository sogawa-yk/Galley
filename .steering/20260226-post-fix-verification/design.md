# 設計書

## D-1: OKE Node Poolイメージデータソース修正

### 変更箇所
- `src/galley/services/design.py`: `_TF_DATA_SOURCES["oke"]`のイメージデータソース定義

### 修正内容
`oci_core_images` データソースに `shape` パラメータを追加し、テンプレートで使用するノードシェイプと互換性のあるイメージのみを取得する。

```hcl
data "oci_core_images" "oke_node" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Standard.E4.Flex"  # 追加
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}
```

### テスト
- 既存テスト: `TestOkeNodePool` がパスすることを確認
- 追加テスト: データソースに`shape`パラメータが含まれることを確認

## D-2: ADB `is_access_control_enabled` 除去

### 変更箇所
- `src/galley/services/design.py`: `_render_component_tf()` のADBプライベートエンドポイント設定

### 修正内容
`is_access_control_enabled = true` をADBプライベートエンドポイントブロックから削除する。

**修正前**:
```python
params["adb_private_endpoint_block"] = (
    "  subnet_id              = var.subnet_id\n"
    "  nsg_ids               = []\n"
    "  is_access_control_enabled = true\n"
)
```

**修正後**:
```python
params["adb_private_endpoint_block"] = (
    "  subnet_id              = var.subnet_id\n"
    "  nsg_ids               = []\n"
)
```

### テスト
- 既存テスト: `TestAdbPrivateEndpoint` を修正（`is_access_control_enabled`のアサーション削除）
- 追加テスト: ADB private endpointに`is_access_control_enabled`が含まれないことを確認
