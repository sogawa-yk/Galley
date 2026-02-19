# 要求内容

## 概要

Phase 4: インフラ層として、Galleyコンテナ内でのTerraform実行、OCI CLIコマンド実行、OCI SDK API呼び出し、Resource Manager連携の機能を実装する。

## 背景

Phase 1〜3でヒアリング・設計層が完成した。次のステップとして、設計したアーキテクチャを実際のOCIインフラとしてプロビジョニングするためのインフラ操作機能が必要。これにより「ヒアリング→設計→インフラ構築」の一貫したワークフローが完成する。

## 実装対象の機能

### 1. F8: ローカルTerraform実行
- Galleyコンテナ内でTerraformコマンド（plan / apply / destroy）を実行
- Terraform stateをローカルファイルシステムに保存（将来的にObject Storage移行）
- LLMがエラーを解析→修正→再実行する自動デバッグループを支援する構造化レスポンス

### 2. F9: OCI操作ツール
- OCI CLIコマンドの実行（ホワイトリスト方式でコマンド検証）
- OCI SDK for Pythonによる構造化API呼び出し

### 3. F10: Resource Manager連携
- Resource Managerスタックの作成
- Plan / Applyジョブの実行
- ジョブ状態とログの取得

## 受け入れ条件

### F8: ローカルTerraform実行
- [ ] `run_terraform_plan` でplan結果（成功またはエラー詳細）を返す
- [ ] `run_terraform_apply` でapplyを実行できる
- [ ] `run_terraform_destroy` でリソースをクリーンアップできる
- [ ] Terraform stateがローカルファイルシステムに保存される
- [ ] 構造化されたエラーレスポンスにより、LLMが自動デバッグループを実行できる

### F9: OCI操作ツール
- [ ] `run_oci_cli` で任意のOCI CLIコマンドを実行し、結果を返す
- [ ] `oci_sdk_call` でOCI SDK for Pythonを利用した構造化API呼び出しができる
- [ ] OCI CLIコマンドのホワイトリスト検証によりシェルインジェクションを防止

### F10: Resource Manager連携
- [ ] `create_rm_stack` でResource Managerスタックを作成できる
- [ ] `run_rm_plan` でPlanジョブを実行できる
- [ ] `run_rm_apply` でApplyジョブを実行できる
- [ ] `get_rm_job_status` でジョブ状態とログを取得できる

## 成功指標

- 全MCPツールが正常に登録され、MCPプロトコル経由で呼び出し可能
- ユニットテストカバレッジ80%以上
- 全テスト、リント、型チェックがパス

## スコープ外

以下はこのフェーズでは実装しません:

- Object Storage へのTerraform state保存（ローカルファイルシステムを使用）
- 実際のOCI API呼び出し（テストはモックで実施）
- E2Eテスト（実際のOCI環境でのテスト）
- Terraform / OCI CLI のコンテナへの同梱（Dockerfile変更は別タスク）

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書（F8, F9, F10）
- `docs/functional-design.md` - 機能設計書（InfraService、UC3）
- `docs/architecture.md` - アーキテクチャ設計書（セキュリティ、パフォーマンス）
