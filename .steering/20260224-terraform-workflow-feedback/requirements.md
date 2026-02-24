# 要求仕様: Terraform ワークフロー フィードバック修正

**元フィードバック**: `docs/feedbacks/feedback.md`

## 修正対象

### P0: terraform init が実行できない
- `run_terraform_plan` / `run_terraform_apply` の事前に `terraform init` を自動実行する

### P1: ファイル配置パスが不明瞭
- `export_iac` のレスポンスに `terraform_dir` のフルパスを含める

### P1: export_iac がスケルトン（コメントアウト）のみ
- サービスタイプごとに実際に動作するリソース定義を生成する
- コンポーネントに応じた追加変数・data sourceを自動生成する

### P2: ヒアリング完了 → アーキテクチャ保存の断絶
- `complete_hearing` のレスポンスに次のステップを案内する

### P2: plan 実行時の変数注入の仕組みがない
- `run_terraform_plan` / `apply` / `destroy` に `variables` パラメータを追加する
