# 要求内容

## 概要

複雑構成（19コンポーネント）のプロビジョニングテストで発見されたIaC生成バグ8件と、バリデーション偽陰性を修正する。

## 背景

`docs/feedbacks/20260226-complex-provisioning-report.md` に記録された通り、IoTリアルタイムデータ分析プラットフォーム（19コンポーネント構成）のTerraform Apply時に8件のエラーが発生。根本原因はIaC生成ロジック（`src/galley/services/design.py`）にある。

主な問題:
1. サブネット割り当てロジックが複数サブネットに対応できない
2. OCI APIリソース名にスペースが含まれる
3. API Gateway endpoint_typeが小文字
4. Private Route TableがIGWを参照
5. Public SubnetにPrivate Route Tableが割り当て
6. OKE Node Poolリソースが未生成
7. ADBプライベートエンドポイント設定が反映されない
8. バリデーションが上記問題を検出できない（偽陰性）

## 実装対象の機能

### 1. サブネット割り当てロジックの修正（C-1）
- `_build_local_references()`が複数サブネットを区別し、connections定義の`deployed_in`関係に基づいて各リソースを正しいサブネットに配置する
- 複数サブネットがある場合、publicリソース（LB, API GW, OKE endpoint）はpublic subnetを参照

### 2. OCI APIリソース名のサニタイズ（C-2）
- NoSQLテーブル名とObject Storageバケット名にサニタイズ済みの名前を使用
- `display_name`は人間可読のまま維持し、`name`フィールドはOCI命名規則に準拠

### 3. API Gateway endpoint_typeの大文字化（C-5）
- `_render_component_tf()`でAPI Gatewayの`endpoint_type`を大文字に変換

### 4. ルートテーブル・ゲートウェイ参照の修正（C-3, C-4）
- Public Route TableはIGWを参照、Private Route TableはNAT GWを参照
- Public SubnetにはPublic Route Table/Security Listを割り当て

### 5. OKE Node Pool生成（H-1）
- OKEクラスタテンプレートにNode Poolリソースを追加

### 6. ADBプライベートエンドポイント対応（H-2）
- endpoint_type=private時にsubnet_idとnsg_idsを設定

### 7. バリデーション強化（M-1）
- ネットワーク整合性チェック（publicリソースのprivateサブネット配置検出）
- リソース名の命名規則チェック（スペース含み検出）

## 受け入れ条件

### サブネット割り当て
- [ ] 複数サブネット構成でpublicリソースがpublic subnetを参照する
- [ ] private subnetに配置すべきリソースがprivate subnetを参照する

### リソース名サニタイズ
- [ ] NoSQLテーブル名に英数字と`_`のみが使用される
- [ ] Object Storageバケット名に英数字、`-`、`_`のみが使用される

### endpoint_type
- [ ] API Gatewayのendpoint_typeが大文字（`PUBLIC`/`PRIVATE`）で出力される

### ルートテーブル・ゲートウェイ
- [ ] Public Route TableがIGWを参照する
- [ ] Private Route TableがNAT GWを参照する
- [ ] Public SubnetにPublic Route Table/Security Listが割り当てられる

### OKE Node Pool
- [ ] OKEクラスタにNode Poolリソースが生成される

### ADBプライベートエンドポイント
- [ ] endpoint_type=private時にsubnet_idが設定される

### バリデーション
- [ ] publicリソースのprivateサブネット配置が検出される
- [ ] リソース名にスペースが含まれる場合に警告が出る

## 成功指標

- `uv run pytest` 全テストパス
- `uv run ruff check src/ tests/` エラーなし
- `uv run mypy src/` エラーなし
- 既存テストが壊れない

## スコープ外

- クォータ事前チェック（M-2, M-3, M-4）— OCI Limitsサービス連携は中期課題
- 非同期Applyワークフロー（L-1）— 別途改善
- 環境変数バリデーション（L-2）— 別途改善
- ツールパラメータdescription追加 — 別途改善

## 参照ドキュメント

- `docs/feedbacks/20260226-complex-provisioning-report.md` - フィードバックレポート
- `docs/development-guidelines.md` - 開発ガイドライン
