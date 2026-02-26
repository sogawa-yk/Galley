# 要求仕様

## 元フィードバック
`docs/feedbacks/20260226-2.md`

## 対応スコープ

### C2: `export_all` が最新のファイル内容を返すべき
- `update_terraform_file`で修正したファイルが`export_all`に反映されない
- exportは常にセッション内の最新ファイル内容を返すべき

### C3: Terraform初期テンプレートの品質改善
- Service Gatewayのサービス選択がリージョン依存（`all-nrt-services-...`がハードコード）
- `data.oci_core_services`からの動的取得をデフォルトにすべき
- ノードプールのsubnet_idが間違ったサブネットを指す問題
- セキュリティリストのTCPポートが`min=0, max=0`で無効
- OKEクラスタに`service_lb_subnet_ids`が未設定
- private route tableにService Gatewayルートが未設定

### スコープ外（別タスク）
- C1: `build_and_deploy`実装 → `/add-feature`で対応
- I1-I4, N1-N5: 設計改善・機能追加 → 別途対応
