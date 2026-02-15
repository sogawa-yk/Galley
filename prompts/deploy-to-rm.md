# OCI Resource Manager デプロイ

エクスポート済みのTerraformファイルをOCI Resource Managerにデプロイします。

## 前提条件

1. `oci` CLIがインストール・設定済みであること
2. `zip` コマンドが利用可能であること
3. セッションでTerraformファイルがエクスポート済みであること

まず `check_oci_cli` ツールで環境を確認してください。

## デプロイフロー

### フローA: Plan → 確認 → Apply（推奨）

1. **スタック作成**: `create_rm_stack` でTerraformファイルをZIP化してResource Managerスタックを作成
2. **Plan実行**: `run_rm_plan` でPlanジョブを実行（非同期）
3. **状態確認**: `get_rm_job_status` でPlanジョブの完了を待機
4. **ユーザー確認**: Plan結果をユーザーに提示し、Apply実行の承認を得る
5. **Apply実行**: `run_rm_apply` で `execution_plan_strategy: FROM_PLAN_JOB_ID` を指定してApply
6. **完了確認**: `get_rm_job_status` でApplyジョブの完了を確認

### フローB: AUTO_APPROVED（デモ・検証用）

1. **スタック作成**: `create_rm_stack` でスタックを作成
2. **Apply実行**: `run_rm_apply` で `execution_plan_strategy: AUTO_APPROVED` を指定
3. **完了確認**: `get_rm_job_status` で完了を確認

## 注意事項

- Resource Managerは `tenancy_ocid`、`region`、`compartment_ocid` を自動注入します
- Plan/Applyジョブは非同期で実行されます。`get_rm_job_status` で状態を確認してください
- `include_logs: true` を指定するとジョブのTerraformログも取得できます
- 本番環境ではフローA（Plan確認あり）を推奨します

## セッションID

{{session_id}}
