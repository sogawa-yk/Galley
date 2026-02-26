# 設計書

## アーキテクチャ概要

変更はすべて `src/galley/services/design.py` とそのテスト `tests/unit/services/test_design.py` に限定される。モデル層・ツール層・インフラ層への変更は不要。

## コンポーネント設計

### 1. リソース名サニタイズ (`_sanitize_resource_name`)

**責務**: display_nameをTerraform/Mermaid互換の安全な識別子に変換する

**実装の要点**:
- `_render_component_tf`、`_build_local_references`、`export_mermaid`で使用される同一のサニタイズロジックを共通化
- `re.sub(r'[^a-z0-9_]', '', name.replace(" ", "_").replace("-", "_").lower())`
- 先頭が数字の場合は `_` をプレフィックス（Terraform制約）

### 2. VCNネットワーク自動展開 (`_expand_vcn_network`)

**責務**: VCNコンポーネントがある場合、欠落しているネットワークリソースを自動補完する

**実装の要点**:
- `export_iac`メソッド内で呼び出し、レンダリング前にコンポーネントリストを拡張
- 元のアーキテクチャオブジェクトは変更しない（export用のローカルコピーを操作）
- 自動生成対象: subnet, internet_gateway, route_table, security_list
- 各VCNに対して1セットのネットワークリソースを生成
- VCNのCIDRブロックからサブネットCIDRを導出（デフォルト: 10.0.1.0/24）

**自動生成ルール**:
```
VCNあり → 以下を確認:
  subnetなし → パブリックサブネットを自動追加
  internet_gatewayなし → IGWを自動追加
  route_tableなし → ルートテーブルを自動追加（IGWへのルート）
  security_listなし → セキュリティリストを自動追加（SSH + HTTPS ingress）
```

### 3. ローカル参照マップの拡張 (`_build_local_references`)

**責務**: VCN関連リソース間の参照を自動解決する

**実装の要点**:
- 既存: `subnet` → `var.subnet_id`, `vcn` → `var.vcn_id`
- 追加: `internet_gateway` → `var.gateway_id`, `route_table` → `var.route_table_id`, `security_list` → `var.security_list_id`

### 4. subnetテンプレートの拡張

**変更内容**:
- `route_table_id` と `security_list_ids` 属性を追加
- 対応する `_TF_REQUIRED_VARS["subnet"]` にも追加
- ローカル参照で自動解決される

### 5. Computeイメージdata source

**変更内容**:
- `_TF_REQUIRED_DATA_SOURCES["compute"]` に `data "oci_core_images"` を追加
- Computeテンプレートの `source_id` を `data.oci_core_images.latest.images[0].id` に変更
- `_TF_REQUIRED_VARS["compute"]` から `image_id` を削除

### 6. ADB `is_free_tier`テンプレート修正

**変更内容**:
- ADBテンプレートの `is_free_tier = false` → `is_free_tier = {is_free_tier}` に変更
- `_TF_DEFAULTS["adb"]` に `"is_free_tier": "false"` を追加

### 7. Mermaid display_name IDs

**変更内容**:
- `export_mermaid`で`comp.id`（UUID）の代わりに`_sanitize_resource_name(comp.display_name)`を使用
- 重複対策: 同名のコンポーネントがある場合はサフィックスを付与

## データフロー

### export_iac（改善後）
```
1. アーキテクチャからコンポーネントリストを取得
2. _expand_vcn_network() でネットワークリソースを自動補完
3. _build_local_references() でローカル参照マップを構築（拡張版）
4. 各コンポーネントを _render_component_tf() でレンダリング
5. ローカル参照を適用
6. ファイル出力
```

## テスト戦略

### ユニットテスト

- `_sanitize_resource_name`: 括弧、特殊文字、先頭数字のテスト
- `_expand_vcn_network`: VCN+Compute構成での自動展開テスト、既存subnet存在時のスキップテスト
- `export_iac`: VCN+Compute構成での統合テスト
- `export_iac`: ADB `is_free_tier` の config 反映テスト
- `export_iac`: Computeイメージdata sourceテスト
- `export_mermaid`: display_nameベースIDのテスト

## ディレクトリ構造

```
src/galley/services/design.py  ← 主な変更対象
tests/unit/services/test_design.py  ← テスト追加
```

## 実装の順序

1. `_sanitize_resource_name`ヘルパー追加・既存コード置換
2. ADB `is_free_tier`テンプレート修正
3. Computeイメージdata source追加
4. ローカル参照マップ拡張
5. subnetテンプレート拡張
6. VCNネットワーク自動展開
7. Mermaid display_name IDs
8. テスト追加・既存テスト更新
