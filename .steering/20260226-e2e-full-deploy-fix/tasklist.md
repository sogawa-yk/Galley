# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

---

## フェーズ1: サブネットCIDR動的算出 + Private SL ingress source修正（問題1,3）

- [x] `design.py` に `_derive_subnet_cidrs(vcn_cidr)` 静的メソッドを追加
- [x] `_expand_vcn_network` のサブネット生成でハードコードCIDRを動的算出に置換
- [x] `_expand_vcn_network` のPrivate Security Listの `ingress_source` をVCN CIDRに動的化

## フェーズ2: OKE用Security Listルール追加（問題2）

- [x] `_TF_RESOURCE_TEMPLATES["security_list"]` テンプレートに `{additional_ingress_rules}` プレースホルダーを追加
- [x] `_TF_DEFAULTS["security_list"]` に `"additional_ingress_rules": ""` デフォルトを追加
- [x] `_expand_vcn_network` でOKE存在時にSecurity List configに追加ルール文字列を注入

## フェーズ3: 未使用変数 `node_subnet_id` の除去（問題4）

- [x] `_build_local_references` で private subnet がある場合に `"var.node_subnet_id"` もマップに追加

## フェーズ4: outputs.tf 自動生成（問題5）

- [x] `export_iac` メソッドにoutputs.tf生成ロジックを追加

## フェーズ5: テスト追加・修正

- [x] カスタムVCN CIDRでサブネットCIDRが正しいことをテスト
- [x] Private SLのingress sourceがVCN CIDRと一致することをテスト
- [x] OKE構成でSLに追加ルールが含まれることをテスト
- [x] OKEなし構成でSLに追加ルールが含まれないことをテスト
- [x] VCN+OKE構成で `node_subnet_id` が variables.tf にないことをテスト
- [x] OKE構成で outputs.tf に `oke_cluster_id` が含まれることをテスト
- [x] VCN構成で outputs.tf に `vcn_id` が含まれることをテスト
- [x] ~~既存テストの修正（VCN同梱OKEの node_subnet_id テスト等）~~（実装方針変更により不要: 既存テストはVCNなしOKEを対象としており、そのまま正常にパスする）

---

## 実装後の振り返り

### 実装完了日
2026-02-26

### 計画と実績の差分

**計画と異なった点**:
- 既存テスト `test_export_iac_oke_node_pool_uses_node_subnet_id` の修正が不要だった。このテストはVCNなしOKE構成をテストしており、`_build_local_references` にprivate subnetが存在しないためvar.node_subnet_idが追加されず、従来通り variables.tf に宣言される。

**新たに必要になったタスク**:
- Ruff F541（不要なf-stringプレフィックス）の修正。outputs.tf生成コードで補間不要な行にf-stringを使用していた。implementation-validatorが検出。

### 学んだこと

**技術的な学び**:
- `ipaddress` 標準ライブラリのIP整数演算（`int(network.network_address) + offset`）で簡潔にサブネットCIDR算出が可能
- Security Listテンプレートの拡張は `{additional_ingress_rules}` プレースホルダーパターンが他のテンプレート（route_tableの `{sgw_route_block}`）と一貫
- `_build_local_references` の `var.*` キーに追加するだけで `locally_provided_vars` フィルタが自動的にvariables.tfから除外してくれる設計が良い

### 次回への改善提案
- `_derive_subnet_cidrs` にVCNプレフィックス長のバリデーション（`/24`以上のVCNでサブネットがVCN外になるケース）を追加すると堅牢性が向上する
- outputs.tfで複数VCN/OKEが存在する場合の出力名重複を検討する（現状は単一VCN/OKE前提）
