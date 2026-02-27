# 設計書

## アーキテクチャ概要

全修正は `src/galley/services/design.py` の Terraform 生成ロジックに集中。テンプレートデータ構造と `_expand_vcn_network` メソッドの改修が中心。

## コンポーネント設計

### 1. サブネットCIDR動的算出

**対象**: `_expand_vcn_network()` line 937-953

**方針**: `ipaddress` 標準ライブラリでVCN CIDRからサブネットを算出する静的メソッドを追加。

### 2. Security Listルール拡張

**対象**: テンプレート + `_expand_vcn_network()`

**方針**: テンプレートに `{additional_ingress_rules}` を追加。OKE存在時に追加ルール文字列をconfigに注入。

### 3. Private SL ingress source動的化

**対象**: `_expand_vcn_network()` line 906

**方針**: VCN CIDRを参照して動的に設定。

### 4. 未使用変数除去

**対象**: `_build_local_references()` line 700-791

**方針**: private subnet がある場合に `"var.node_subnet_id"` をマップに追加。

### 5. outputs.tf 自動生成

**対象**: `export_iac()` line 1016-1152

**方針**: 展開後コンポーネントを走査し、OKE/VCN の output を生成。

## テスト戦略

### ユニットテスト（追加）
- カスタムVCN CIDRでサブネット正しいか
- Private SLのingress sourceがVCN CIDR一致
- OKE構成でSLに追加ルールあり
- OKEなし構成でSLに追加ルールなし
- VCN+OKE構成で node_subnet_id が variables.tf にない
- OKE構成で outputs.tf 生成
- VCN構成で vcn_id output 生成

## 変更ファイル

```
src/galley/services/design.py      # メイン修正
tests/unit/services/test_design.py  # テスト追加・修正
```
