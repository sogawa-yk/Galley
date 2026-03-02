# E2E Todo App デプロイテスト (OKE + ADB構成)

**テスト実施日**: 2026-03-02
**テストツール**: mcp-gauge (E2Eフルデプロイテスト)
**テスト環境**: ap-osaka-1
**テスト構成**: VCN + OKE (1ノード) + ADB (ATP, Private Endpoint)
**テスト結果**: アプリデプロイ成功（ADBはテナンシー制限で失敗、in-memoryフォールバック動作）

---

## テスト概要

Galleyのフルワークフロー（ヒアリング→設計→IaC生成→Terraform apply→テンプレートスキャフォールド→アプリカスタマイズ→ビルド→デプロイ）をmcp-gaugeで実行。OKE上にTodo REST APIアプリをデプロイし、全CRUD操作の正常動作を確認。

**mcp-gaugeメトリクス**: 20ツール呼出、14種類使用、0エラー、必須11ツール全カバー

---

## 問題1: ADB作成時の409-IncorrectStateエラーの事前検出不足

**重要度**: High
**対象ファイル**: `src/galley/validators/architecture.py`, `src/galley/services/infra.py`

**症状**: `save_architecture`でADBを含む構成を保存し、`validate_architecture`がエラーなし(0警告)で通過したにもかかわらず、Terraform apply時に`409-IncorrectState: You are attempting to use a feature that's not currently enabled for this tenancy`で失敗。20分近い待ち時間の後に初めてエラーが判明する。

**期待動作**:
- `validate_architecture`で、ADBがテナンシーで利用可能かどうかを事前チェックし、警告を出す
- または、`export_iac`時にADBサービスの利用可能性をOCI APIで確認し、不可の場合はユーザーに通知する

**改善提案**:
- `validate_architecture`に`run_oci_cli`で `oci db autonomous-database list --compartment-id ... --limit 1` を実行し、権限/機能の有効性をプリフライトチェックするオプションを追加
- エラーメッセージに「テナンシーでADB機能を有効化するにはOracle Supportへの問い合わせが必要」等の具体的なガイダンスを含める

---

## 問題2: K8sリソース名がapp_nameパラメータではなくテンプレート名を使用

**重要度**: Medium
**対象ファイル**: `src/galley/services/app.py` (K8sマニフェスト生成部分)

**症状**: `scaffold_from_template`で`app_name: "todo-app"`を指定したが、生成されるK8s Deployment/Serviceのリソース名が`rest-api-adb`（テンプレート名）になる。

**再現手順**:
1. `scaffold_from_template(template_name="rest-api-adb", params={"app_name": "todo-app"})`
2. `build_and_deploy`実行
3. `kubectl get all` → `deployment.apps/rest-api-adb`, `service/rest-api-adb` が確認される

**期待動作**: K8sリソース名にはユーザーが指定した`app_name`パラメータ（`todo-app`）が使われるべき。

**原因推定**: `_get_app_name()`メソッドがテンプレートメタデータの`name`フィールドを返している可能性。`params`から`app_name`を取得するロジックに変更が必要。

---

## 問題3: `check_app_status`がendpointを返さない

**重要度**: Medium
**対象ファイル**: `src/galley/services/app.py` (`check_app_status`メソッド)

**症状**: `build_and_deploy`が成功し、実際にLoadBalancer IPが割り当てられている状態でも、`check_app_status`の`endpoint`がnullで返される。

**再現手順**:
1. `build_and_deploy`実行 → success=true, endpoint=null
2. `check_app_status`実行 → endpoint=null
3. `kubectl get svc rest-api-adb` → EXTERNAL-IP=64.110.110.193 が確認できる

**期待動作**: LoadBalancer IPが割り当てられていれば、`check_app_status`の`endpoint`フィールドにURLが返されるべき。

**原因推定**:
- `build_and_deploy`のendpoint取得はLB IPが`<pending>`の間はnullを返す（タイミング問題）
- `check_app_status`はService名を正しく参照できていない可能性（テンプレート名 vs app_name問題に関連）

---

## 問題4: `run_terraform_apply`のタイムアウト時にRMジョブIDが返されない

**重要度**: Medium
**対象ファイル**: `src/galley/services/infra.py`

**症状**: `run_terraform_apply`が300秒タイムアウトすると、エラーメッセージのみが返され、実行中のRMジョブIDが含まれない。ユーザーは`run_oci_cli`でスタック/ジョブを手動検索する必要がある。

**期待動作**: タイムアウト時のレスポンスに`job_id`を含め、`get_rm_job_status`でポーリングできるようにする。例:
```json
{
  "error": "timeout",
  "message": "Apply job timed out after 300s. Job is still running.",
  "job_id": "ocid1.ormjob.oc1...",
  "suggestion": "Use get_rm_job_status to check progress"
}
```

---

## 問題5: `run_oci_cli`でOKE (ce) コマンドが許可されていない

**重要度**: Medium
**対象ファイル**: `src/galley/services/infra.py` (OCI CLIコマンド許可リスト)

**症状**: `oci ce cluster list`を実行すると`CommandNotAllowedError`が返される。OKEクラスタの情報取得（OCID、エンドポイント等）をOCI CLI経由で確認できない。

**期待動作**: OKEを含むアーキテクチャを生成する以上、以下のCEコマンドを許可リストに追加すべき:
- `oci ce cluster list`
- `oci ce cluster get`
- `oci ce node-pool list`
- `oci ce node-pool get`

---

## 問題6: outputs.tfにADB関連の出力が含まれない

**重要度**: Low
**対象ファイル**: `src/galley/services/design.py` (outputs.tf生成部分)

**症状**: ADBを含む構成でも`outputs.tf`には`vcn_id`と`oke_cluster_id`のみ。ADBのOCID、接続文字列、ウォレットダウンロード情報が出力されない。

**期待動作**: ADBコンポーネントが存在する場合、以下の出力を追加:
```hcl
output "adb_id" {
  description = "Autonomous Database OCID"
  value       = oci_database_autonomous_database.todo_adb.id
}
output "adb_connection_strings" {
  description = "ADB connection strings"
  value       = oci_database_autonomous_database.todo_adb.connection_strings
}
```

---

## 問題7: Terraform apply部分的失敗時の復旧ガイダンス不足

**重要度**: Low
**対象**: ワークフロー全体

**症状**: ADB作成が失敗したが、VCN + OKE は正常に作成された。この部分的な成功/失敗状態について、Galleyからユーザーへの明確なガイダンスがない。

**期待動作**:
- `get_rm_job_status`のレスポンスに、成功したリソースと失敗したリソースの一覧を含める
- 部分的失敗時の推奨アクション（再apply、構成変更、destroy等）を提案する

---

## 問題8: テンプレートのdb.pyがスタブ実装

**重要度**: Low
**対象ファイル**: `config/templates/rest-api-adb/app/src/db.py`

**症状**: テンプレートの`src/db.py`（protected file）の`get_db_pool()`がpass文のみで、実際のDB接続プール初期化ロジックがない。routes.pyで個別にconnection管理を実装する必要がある。

**期待動作**: テンプレートの`db.py`に、oracledbを使った実用的な接続プール管理の実装を含めるべき。protected fileなのでユーザーが変更できないため、テンプレート自体を改善する必要がある。

---

## 補足

- OKEクラスタ作成: 7分1秒、ノードプール作成: 12分10秒（合計約19分）
- ADBは約19分後に409エラーで失敗（テナンシーのADB機能未有効化）
- Todoアプリはin-memoryフォールバックで全CRUD正常動作確認
- mcp-gauge評価: PASSED (20呼出、0エラー)
- クラスタID: `ocid1.cluster.oc1.ap-osaka-1.aaaaaaaaurkuc4as776i5sapq7zk7rw3pcn65ivuw6osnvykbcthwsi5nfkq`
- ノードプールID: `ocid1.nodepool.oc1.ap-osaka-1.aaaaaaaav3c4p3xmjrdltw2r4ew7t4ynod7m4czpap7gevepunjvgahj6yza`
- LoadBalancer IP: `64.110.110.193`
- RMスタックID: `ocid1.ormstack.oc1.ap-osaka-1.amaaaaaassl65iqa5zsblmmjscejhcequr2w4wfbcopkfhac2un46mv75m6q`
