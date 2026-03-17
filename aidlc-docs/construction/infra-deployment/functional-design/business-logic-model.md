# Business Logic Model - Unit 3: Infrastructure Deployment

## Overview

Infrastructure Deployment Skillは3段階のフローで動作する：
1. **準備**: Terraformコードのzip化、コンパートメント解決
2. **Stack作成+Apply**: Resource Manager Stack作成、Plan/Apply実行
3. **結果取得**: Stack Outputs取得、stack_outputs.json出力

## フロー詳細

```
generated/{project-name}/terraform/
      |
      v
[Phase 1: 準備]
      | Terraformディレクトリをzip圧縮
      | コンパートメントID解決（フォールバックチェーン）
      v
[Phase 2: Stack作成+Apply]  <--+
      | oci_rm.create_stack()      |
      | oci_rm.run_plan()          |
      | oci_rm.wait_for_job()      |
      | Plan失敗? -> 修正+再試行 --+ (最大2回)
      | oci_rm.run_apply()         |
      | oci_rm.wait_for_job()      |
      | Apply失敗? -> 修正+再試行 -+ (最大2回)
      v
[Phase 3: 結果取得]
      | oci_rm.get_stack_outputs()
      | -> generated/{project-name}/stack_outputs.json
      v
Complete (後続ユニットへ)
```

## Phase 1: 準備

### Terraformコードのzip化
1. `generated/{project_name}/terraform/` ディレクトリの存在確認
2. ディレクトリ内の全 `.tf` ファイルをzip圧縮
3. zip出力先: `generated/{project_name}/terraform.zip`

### コンパートメントID解決（フォールバックチェーン）
以下の順序でコンパートメントIDを解決する:
1. **インスタンスメタデータ**: インスタンスプリンシパルのメタデータAPIからコンパートメントIDを取得
2. **環境変数**: `OCI_COMPARTMENT_ID` 環境変数から取得
3. **ユーザー入力**: 上記が取得できない場合、Claude CodeがユーザーにコンパートメントIDを質問

## Phase 2: Stack作成+Apply

### Stack作成
- `oci resource-manager stack create` でStack作成
- zip化したTerraformコードをアップロード
- display_name: `{project_name}-stack`
- terraform_version: "1.5.x" 以上

### Plan実行
- `oci resource-manager job create --operation PLAN` でPlan Job実行
- `wait_for_job()` でPlan完了を待機
- Plan結果にエラーがないことを確認

### Apply実行
- Plan成功後、`oci resource-manager job create --operation APPLY` でApply Job実行
- `wait_for_job()` でApply完了を待機（30秒間隔、60分タイムアウト）
- Apply結果の確認

### エラーハンドリング（自己修正ループ）
- **Plan失敗**: ログ取得 → Claude Codeがエラー分析 → Terraformコード修正 → zip再作成 → Stack更新 → Plan再実行（最大2回リトライ）
- **Apply失敗**: ログ取得 → Claude Codeがエラー分析 → Terraformコード修正 → zip再作成 → Stack更新 → Plan再実行 → Apply再実行（最大2回リトライ）。部分作成済みリソースはTerraform stateが管理するため差分適用される
- **修正不能なエラー**: 権限不足、サービス制限等はユーザーに報告
- **タイムアウト**: 現在のJob状態を報告し、ユーザーに判断を委ねる

## Phase 3: 結果取得

### Stack Outputs取得
- Apply成功後、`oci resource-manager job get-job-detailed-log-content` でoutputsを取得
- もしくは `oci resource-manager stack list-terraform-versions` + output取得

### stack_outputs.json生成
- Terraform outputsをJSON形式で `generated/{project_name}/stack_outputs.json` に保存
- 後続ユニット（deploy-app, verify）がこのファイルを参照
