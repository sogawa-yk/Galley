# 要求内容

## 概要

`export_iac`が生成するTerraformコードの品質を向上させ、手動修正なしでPlan/Applyが通る実用的なIaCコードを生成する。

## 背景

Compute + ADB (ATP) 構成の検証で、生成されたTerraformコードに複数の問題が見つかり、手動修正が必要だった。フィードバック: `docs/feedbacks/20260226.md`

## 実装対象の機能

### 1. リソース名のサニタイズ強化
- `autonomous_db_(atp)` のような括弧を含む名前がTerraformリソース名に使用され、Plan失敗を引き起こす
- 英数字・アンダースコア以外の文字を除去する正規表現ベースのサニタイズを導入

### 2. VCNネットワークリソースの自動生成
- VCNのみの定義では、サブネット・IGW・ルートテーブル・セキュリティリストが未生成でComputeが配置できない
- VCNがアーキテクチャに含まれる場合、関連するネットワークリソースを自動補完する

### 3. Compute用イメージの自動取得
- `var.image_id`（外部変数依存）→ `data "oci_core_images"` による自動取得に変更
- 検証用途で手動OCID設定が不要になる

### 4. ADB `is_free_tier`のconfig反映
- ADBテンプレートの`is_free_tier = false`がハードコード → configの値を反映するよう修正

### 5. Mermaid構成図の可読性向上
- ノードIDがUUID → display_nameベースの安全な識別子に変更

## 受け入れ条件

### リソース名サニタイズ
- [ ] `autonomous_db_(atp)` → `autonomous_db_atp` に変換される
- [ ] 英数字・アンダースコア以外の文字がすべて除去される
- [ ] 既存の空白→`_`、ハイフン→`_`、小文字変換も維持

### VCNネットワーク自動生成
- [ ] VCN+Computeの構成でexport_iacすると、subnet/IGW/route_table/security_listが自動生成される
- [ ] 自動生成されたリソース間の参照（var.vcn_id → oci_core_vcn.xxx.id等）が正しい
- [ ] ユーザーが明示的にsubnetを定義済みの場合は自動生成しない

### Computeイメージ自動取得
- [ ] Compute含むアーキテクチャのmain.tfに`data "oci_core_images"`が含まれる
- [ ] Computeテンプレートの`source_id`がdata sourceを参照する
- [ ] variables.tfに`image_id`変数が生成されない

### ADB is_free_tier
- [ ] `config: {"is_free_tier": True}` → Terraformコード上で `is_free_tier = true` になる
- [ ] configが未設定の場合はデフォルト値`false`が使用される

### Mermaid可読性
- [ ] MermaidノードIDがdisplay_nameベースの安全な文字列になる
- [ ] 接続エッジが正しく描画される

## スコープ外

- ジョブ管理・ロック制御の改善（別タスク: アーキテクチャ変更が必要）
- 部分適用時のリカバリ機能（別タスク）
- unlock_sessionツールの追加（機能リクエスト）
- ヒアリング→IaCの完全な情報伝達パイプライン（別タスク）
- コスト見積もり機能（機能リクエスト）

## 参照ドキュメント

- `docs/feedbacks/20260226.md` - フィードバック元
- `docs/architecture.md` - 技術仕様書
- `docs/development-guidelines.md` - 開発ガイドライン
