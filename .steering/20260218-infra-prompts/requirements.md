# 要件定義: インフラ層プロンプト追加

## 目的

Phase4で実装したインフラ層ツール（Terraform実行、OCI CLI、Resource Manager）を、LLMが自然に活用できるようMCPプロンプトを追加する。

## スコープ

### 対象機能
- F8: ローカルTerraform実行のガイダンスプロンプト
- F9: OCI操作ツールのガイダンスプロンプト

### 対象外
- F10のResource Manager関連プロンプト（全メソッドがスタブ実装のため不要）
- アプリケーション層（Phase 5）のプロンプト

## 要件

### RQ1: Terraform自動デバッグループプロンプト
- 設計済みアーキテクチャからTerraformコードを生成し、plan→apply→エラー修正の自動デバッグループを実行するフローをガイドする
- `export_iac` → `run_terraform_plan` → （エラーあれば修正して再実行）→ `run_terraform_apply` の流れ
- エラー時はstdoutとstderrを分析してTerraformコードを修正し、再度planを実行する指示

### RQ2: OCI情報確認プロンプト
- `run_oci_cli` を使ってOCIリソースの情報を確認・調査するフローをガイドする
- 許可されているサービスコマンドの例示
- JSON出力のパース方法の示唆

### RQ3: インフラクリーンアッププロンプト
- `run_terraform_destroy` による環境破棄のフローをガイドする
- 破棄前の確認（planでの変更内容確認）を促す

## 既存パターンとの整合性
- `prompts/hearing.py` と `prompts/design.py` のパターンを踏襲
- `register_infra_prompts(mcp: FastMCP)` 関数で登録
- `server.py` にインフラプロンプトの登録を追加
- 統合テストでプロンプト登録を検証
