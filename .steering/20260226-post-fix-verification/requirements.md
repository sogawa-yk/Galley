# 要求仕様

## 参照元
- `docs/feedbacks/20260226-post-fix-verification.md`

## 修正対象

### R-1: OKE Node Poolイメージ互換性エラーの修正
- **問題**: `data "oci_core_images" "oke_node"` のフィルタにshapeパラメータがなく、取得されるイメージがFlex shapesと互換性がない
- **エラー**: `400-InvalidParameter, Invalid nodeShape: Node shape and image are not compatible`
- **要求**: OKE Node Pool用のイメージデータソースにshapeフィルタを追加し、Flex shapeと互換性のあるイメージを取得する

### R-2: ADB `is_access_control_enabled` パラメータの削除
- **問題**: ADBプライベートエンドポイント設定に`is_access_control_enabled = true`を含めているが、一部のADB種別で非対応
- **エラー**: `400-InvalidParameter, Configure access control for Autonomous AI Database is not supported`
- **要求**: プライベートエンドポイント設定から`is_access_control_enabled`を除去し、`subnet_id`と`nsg_ids`のみとする
