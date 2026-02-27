# 要求内容

## 概要

E2Eフルデプロイテストで発見された5つのIaC生成バグを修正し、VCN+OKE構成のTerraformが手動修正なしで正常にapplyできるようにする。

## 背景

`docs/feedbacks/20260226-e2e-full-deploy.md` に記載の通り、Galleyの `export_iac` が生成するTerraformコードには複数の問題があり、OKEクラスタのデプロイに失敗する。E2Eテストでは `update_terraform_file` で手動修正して回避したが、根本修正が必要。

## 実装対象の修正

### 1. サブネットCIDRの動的算出（問題1）
- VCN CIDRからサブネットCIDRを動的に算出する
- 例: VCN `10.100.0.0/16` → Public `10.100.1.0/24`, Private `10.100.2.0/24`

### 2. OKE用Security Listルールの追加（問題2）
- Public Security List: VCN内全TCP許可ルール + ICMP Type 3 Code 4
- Private Security List: VCN内全TCP許可ルール + ICMP Type 3 Code 4

### 3. Private Security Listのingress sourceの動的化（問題3）
- `10.0.0.0/16` ハードコードをVCN CIDRから動的に設定

### 4. 未使用変数 `node_subnet_id` の除去（問題4）
- VCN同梱時に `node_subnet_id` が variables.tf に宣言されないようにする

### 5. Terraform outputs.tf の自動生成（問題5）
- OKEコンポーネントがあれば `oke_cluster_id` outputを生成
- VCNコンポーネントがあれば `vcn_id` outputを生成

## 受け入れ条件

### サブネットCIDR動的算出
- [ ] VCN CIDR `10.100.0.0/16` 時にサブネットが `10.100.1.0/24`, `10.100.2.0/24` になる
- [ ] VCN CIDR `10.0.0.0/16` 時にサブネットが `10.0.1.0/24`, `10.0.2.0/24` になる（後方互換）

### Security Listルール
- [ ] OKEを含む構成でPublic SLにVCN内全TCP許可ルールが含まれる
- [ ] OKEを含む構成でSLにICMP Type 3 Code 4ルールが含まれる
- [ ] OKEを含まない構成ではSLに追加ルールが含まれない

### Private SL ingress source
- [ ] Private SLのingress sourceがVCN CIDRと一致する

### 未使用変数除去
- [ ] VCN同梱時に `node_subnet_id` が variables.tf に出現しない

### outputs.tf生成
- [ ] OKEコンポーネントがあれば `oke_cluster_id` outputが生成される
- [ ] VCNコンポーネントがあれば `vcn_id` outputが生成される

## スコープ外

- 問題6（mcp-gaugeタイムアウト）はGalley外の制約のため対象外

## 参照ドキュメント

- `docs/feedbacks/20260226-e2e-full-deploy.md` - E2Eフルデプロイテストフィードバック
