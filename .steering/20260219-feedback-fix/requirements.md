# 要求仕様: フィードバック修正

## 参照元
- `docs/feedbacks/feedback.md`

## 概要
Claude Desktopからの実操作テスト（ヒアリング→アーキテクチャ設計→Terraform生成・実行）で発見された問題点を修正する。

## 修正項目

### R1: エラーメッセージのガイダンス改善 (FB 2.1)
- `ArchitectureNotFoundError`のメッセージに「先に`save_architecture`を実行してください」を含める
- `complete_hearing`のレスポンスに次ステップ（`save_architecture`）のガイダンスを含める

### R2: `save_architecture`のconnection ID解決 (FB 2.2)
- `save_architecture`で、componentsに仮IDを指定した場合、connectionsのsource_id/target_idも自動的にUUIDにマッピングする
- LLMが`components`配列内で指定した仮IDを、生成されたUUIDに置換する

### R3: `export_iac`のTerraformテンプレート品質改善 (FB 3.1, 3.2)
- TODOコメントのスケルトンではなく、動作するTerraformリソース定義を生成する
- サービスタイプごとに正確なOCI Providerリソース名を使用する
- HCL値にはダブルクォートを使用する（シングルクォート問題の修正）
- 暗黙的に必要なリソース（VCN→サブネット、Functions→Application等）も含める

### R4: `export_iac`のサーバー側ファイル書き出し (FB 4.1)
- `export_iac`実行時にセッションのデータディレクトリにTerraformファイルを書き出す
- レスポンスに書き出し先パス（`terraform_dir`）を含める
- `run_terraform_plan`がそのパスをそのまま受け取れるようにする

### R5: `run_terraform_plan`に自動`terraform init` (FB 4.2)
- `run_terraform_plan`内部で、init未実行を検知した場合に自動的に`terraform init`を実行する
- `.terraform`ディレクトリの存在チェックで判定

### R6: `run_terraform_plan/apply/destroy`に変数パラメータ追加 (FB 4.3)
- `variables: dict[str, str] | None`パラメータを追加
- 内部で`-var key=value`に変換してTerraformコマンドに渡す
