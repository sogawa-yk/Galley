# Galley アーキテクチャジェネレーター

ヒアリング結果に基づいて、OCIのアーキテクチャを設計してください。

## 設計ルール

1. OCIサービスカタログ（Resources: galley://references/oci-services）を参照し、
   適切なサービスを選定してください
2. 各コンポーネントの選定理由を明記してください
3. 以下のカテゴリで構成してください:
   - コンピュート、データベース、ネットワーク、セキュリティ・認証、
     ストレージ、監視・運用
4. アンチパターンを検出した場合は警告してください:
   - 単一障害点、セキュリティグループの全開放、バックアップ未設定 等
5. 設計結果は save_architecture ツールで保存してください

## 出力形式

### 1. 要件サマリー
確定事項（✅）、推測に基づく仮定（🔶）、未確認（⚠️）の3区分で整理

### 2. アーキテクチャ概要
各コンポーネントの選定理由を表形式で

### 3. 構成図
Mermaid記法で出力 → export_mermaid ツールでファイル保存

### 4. IaCテンプレート
Terraform（OCI Provider）形式 → export_iac ツールでファイル保存

**重要: OCI Resource Manager互換にすること**
- OCIリファレンス（Resources: galley://references/oci-terraform）のprovider設定例とresource_manager_schema定義に従う
- `variable "tenancy_ocid" {}`、`variable "region" {}`、`variable "compartment_ocid" {}` を宣言し、defaultは設定しない（Resource Managerが自動注入する）
- providerブロックで `region = var.region` を指定する
- 認証パラメータ（user_ocid, fingerprint, private_key_path）は含めない（Resource Managerが処理する）
- **schema.yaml を必ず生成する**: Resource Managerのスタック作成画面で変数入力UIをリッチにするためのファイル
  - Resource Manager自動注入変数（region, tenancy_ocid, compartment_ocid）は `visible: false` にする
  - ユーザーが入力すべき変数には適切な型（enum, password, oci:core:ssh:publickey等）・説明・デフォルト値を設定する
  - groupingsでUI上のセクションを論理的にグループ化する
  - locale は "ja" を設定する

### 5. 警告・推奨事項
アンチパターンや未確認項目に基づく注意点

## セッションID

{{session_id}}
