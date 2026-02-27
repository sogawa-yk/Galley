# E2Eフルデプロイテスト フィードバックレポート

**テスト実施日**: 2026-02-26
**テストツール**: mcp-gauge
**テスト環境**: ap-osaka-1 (ローカル開発環境からGalleyサーバーを起動)

---

## テスト概要

REST APIアプリケーション(FastAPI)をGalleyの全ワークフローを通じて実際のOKEクラスタにデプロイし、curlで疎通確認まで行うE2Eフルデプロイテスト。

### テスト結果: PASSED

- 総ツール呼び出し: 18回
- 必須ツール網羅: 10/10
- エラー: 1（kubectl未インストール → リカバリ成功）
- 合計所要時間: 約45分（OKEクラスタ作成含む）

---

## 問題1: サブネットCIDRがVCN CIDR範囲外にハードコードされている

**重要度**: Critical
**対象ファイル**: `src/galley/services/design.py`（VCN Terraform生成部分）

**症状**: `export_iac` が生成するサブネットCIDRが `10.0.1.0/24`（Public）、`10.0.2.0/24`（Private）にハードコードされており、VCN CIDRが `10.100.0.0/16` など `10.0.0.0/16` 以外の場合、サブネットがVCN範囲外になる。

**再現手順**:
1. `save_architecture` で VCN の `cidr_block` を `10.100.0.0/16` に設定
2. `export_iac` を実行
3. 生成された `components.tf` のサブネットCIDRが `10.0.1.0/24`, `10.0.2.0/24` になっている

**期待動作**: VCN CIDRからサブネットCIDRを動的に算出する。例: VCN `10.100.0.0/16` → Public `10.100.1.0/24`, Private `10.100.2.0/24`。

**回避策**: `update_terraform_file` でサブネットCIDRを手動修正。

---

## 問題2: OKE用Security Listにルールが不足している

**重要度**: Critical
**対象ファイル**: `src/galley/services/design.py`（Security List Terraform生成部分）

**症状**: 生成されるPublic Security ListにVCN内TCP全ポート許可ルール（OKEオペレーター通信 port 12250等）とICMP Path MTU Discoveryルールが欠落。Private Security ListにもICMPルールが欠落。この結果、OKEノードプールのワーカーノードがAPIサーバーに登録できず、`1 node(s) register timeout` エラーでTerraform applyが失敗する。

**必要なルール**:

Public Security List（追加必要）:
- Ingress: 全TCP from VCN CIDR（OKEオペレーター 12250, kubelet 10250等）
- Ingress: ICMP Type 3 Code 4 from 0.0.0.0/0（Path MTU Discovery）

Private Security List（追加必要）:
- Ingress: ICMP Type 3 Code 4 from 0.0.0.0/0（Path MTU Discovery）

**回避策**: `update_terraform_file` で Security List を手動修正して再apply。

---

## 問題3: Private Security Listのingress sourceがVCN CIDRと不整合

**重要度**: High
**対象ファイル**: `src/galley/services/design.py`

**症状**: Private Security Listのingress sourceが `10.0.0.0/16` にハードコードされており、VCN CIDRが異なる場合にノード間通信がブロックされる。

**期待動作**: VCN CIDRから動的にingress sourceを設定する。

---

## 問題4: 未使用変数 `node_subnet_id` が生成される

**重要度**: Low
**対象ファイル**: `src/galley/services/design.py`（variables.tf生成部分）

**症状**: OKEを含むアーキテクチャで `export_iac` すると、`variables.tf` に `node_subnet_id` 変数が宣言されるが、`components.tf` では使用されていない（ノードプールは `oci_core_subnet.xxx_private_subnet.id` を直接参照）。Resource Managerでは必須変数として値の入力を求められる可能性がある。

**改善案**: `node_subnet_id` 変数の宣言を削除するか、ノードプールの `subnet_id` で実際に参照する。

---

## 問題5: Terraform outputブロックが生成されない

**重要度**: Medium
**対象ファイル**: `src/galley/services/design.py`

**症状**: `export_iac` が `outputs.tf` を生成しない。Terraform apply後にOKEクラスタOCIDやVCN OCIDを取得するには、OCI CLIで別途検索する必要がある。`build_and_deploy` に `cluster_id` を渡す際に不便。

**改善案**: アーキテクチャ内のOKEコンポーネントに対して `output "oke_cluster_id"` を自動生成する。VCN OCIDも同様。

---

## 問題6: `run_terraform_apply` のmcp-gaugeタイムアウト

**重要度**: Medium
**対象**: mcp-gauge側の制約（Galleyのバグではない）

**症状**: OKEクラスタ作成は15-20分かかるが、mcp-gaugeの `gauge_proxy_call` が300秒でタイムアウトする。タイムアウト後もOCI Resource Managerのジョブはバックグラウンドで継続するが、Galley側のレスポンスが返らない。

**回避策**: OCI CLIで直接RMスタックを更新しapplyジョブを作成。ジョブ完了をポーリングで待機。

**改善案**: `run_terraform_apply` にタイムアウト後もジョブIDを返す仕組み、または `get_rm_job_status` で非同期的にポーリングするワークフローを推奨する。

---

## 補足: テストで確認できた正常動作

- `create_session` → `save_answers_batch` → `complete_hearing` のヒアリングフロー
- `save_architecture` によるVCN + OKE構成の保存
- `scaffold_from_template` によるアプリコード生成（パラメータ置換含む）
- `update_app_code` によるコードカスタマイズ（protected_paths以外）
- `export_iac` による Terraform ファイル生成（main.tf, variables.tf, components.tf）
- `update_terraform_file` による Terraform 修正
- `run_terraform_plan` — Resource Manager経由のplan実行・結果取得
- `build_and_deploy` — kubeconfig取得、K8sマニフェスト生成、kubectl apply、rollout status待機、エンドポイント取得
- `check_app_status` — Pod状態確認、LoadBalancer IP取得
- 実際のcurl疎通: 3エンドポイント全て正常レスポンス

---

## 対応結果
- **対応日**: 2026-02-26
- **ステアリング**: `.steering/20260226-e2e-full-deploy-fix/`
- **対応内容の要約**: design.pyの5件のIaC生成バグを修正。(1) サブネットCIDRをVCN CIDRから動的算出、(2) OKE用Security Listに全TCP+ICMPルール追加、(3) Private SL ingress sourceをVCN CIDRに動的化、(4) VCN同梱時の未使用node_subnet_id変数を除去、(5) outputs.tf自動生成。テスト10件追加（90件全パス）。
- **E2Eスモークテスト**: PASSED（VCN 10.254.0.0/16でplan成功、7ツール呼出・0エラー）
