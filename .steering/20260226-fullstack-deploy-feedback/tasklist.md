# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

---

## フェーズ1: 問題調査

- [x] export_all / export_iacの実装を調査し、ファイル内容の返却方法を把握
- [x] design.pyのIaC生成ロジックを調査し、テンプレート品質の問題箇所を特定

## フェーズ2: C2修正 — export_allが最新ファイルを返すよう修正

- [x] `export_all`がterraform_dirの実ファイルを読み返すよう修正（`export_iac`は再生成のまま）
- [x] 関連テストを更新

## フェーズ3: C3修正 — Terraformテンプレート品質改善

- [x] Service Gateway data sourceにregexフィルタを追加し「All * Services」を確実に取得
- [x] route_tableテンプレートにService Gatewayルート（SERVICE_CIDR_BLOCK）をオプション追加
- [x] `_expand_vcn_network`でpublic/private両方のroute_table, security_list, subnetを生成
- [x] OKEテンプレートに`service_lb_subnet_ids`を追加
- [x] OKEのnode_poolがprivateサブネットを参照するよう修正
- [x] セキュリティリストのport=0ガード追加
- [x] 関連テストを更新

## フェーズ4: 品質チェック

- [x] `uv run pytest` — 268 passed
- [x] `uv run ruff check src/ tests/` — All checks passed
- [x] `uv run ruff format --check src/ tests/` — 60 files already formatted
- [x] `uv run mypy src/` — no issues found in 33 source files

---

## 実装後の振り返り

- **実装完了日**: 2026-02-26
- **計画と実績の差分**:
  - 計画通りに全タスクを完了。品質チェックで269テスト通過（計画時268→テスト追加で+1）
  - `export_all`の修正方針を「`export_iac`も変更」から「`export_all`のみディスク読み込み」に限定。`export_iac`は常に再生成する設計を維持した
  - implementation-validatorが`service_lb_subnet_ids`のサブネット誤参照を検出し、修正を追加実施
- **学んだこと**:
  - VCNのネットワーク展開（public/private分離）は多くのサブコンポーネント（IGW, NAT GW, SGW, Route Table×2, Security List×2, Subnet×2）を生成するため、テンプレート設計時に全体の整合性を慎重に管理する必要がある
  - OKEは3つの異なるサブネット参照が必要（API endpoint=public, node pool=private, service LB=public）で、テンプレートの変数マッピングが複雑
  - `data.oci_core_services`のregexフィルタでリージョン非依存なService Gateway設定が実現できる
- **次回への改善提案**:
  - IaC生成のE2Eテスト（VCN plan-only）を自動テストスイートに組み込むことを検討
  - OKE+MySQL等の複合構成に対するE2Eスモークテストの追加
