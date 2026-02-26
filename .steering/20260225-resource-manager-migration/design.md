# 設計書

## アーキテクチャ概要

ローカルTerraform実行をOCI Resource Manager (RM) API経由に置き換える。LLM向けツールインターフェースは維持し、内部実装のみ変更する。

```
[LLM] → run_terraform_plan(session_id, terraform_dir, variables)
         ↓
[InfraService]
  1. terraform_dirをzip化
  2. RMスタック作成 or 更新（zip + variables）
  3. Planジョブ作成
  4. ジョブ完了までポーリング
  5. ログ取得 → TerraformResult形式で返却
```

## コンポーネント設計

### 1. RMクライアント初期化 (`_get_rm_client`)

**責務**:
- OCI Python SDKの`ResourceManagerClient`を遅延初期化
- 環境に応じた認証方式の自動選択（ResourcePrincipal / API Key）

**実装の要点**:
```python
def _get_rm_client(self) -> oci.resource_manager.ResourceManagerClient:
    if self._rm_client is None:
        if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
            signer = oci.auth.signers.get_resource_principals_signer()
            self._rm_client = oci.resource_manager.ResourceManagerClient({}, signer=signer)
        else:
            config = oci.config.from_file()
            self._rm_client = oci.resource_manager.ResourceManagerClient(config)
    return self._rm_client
```

### 2. Terraformファイルのzip化 (`_zip_terraform_dir`)

**責務**:
- terraform_dir配下のファイルをインメモリzipに圧縮
- base64エンコードして返却

**実装の要点**:
- `io.BytesIO` + `zipfile.ZipFile`でインメモリ処理
- `.terraform/`ディレクトリと`*.tfstate*`ファイルは除外
- パスはzip内で相対パスにする

### 3. スタック管理 (`_ensure_rm_stack`)

**責務**:
- セッションにスタックが紐付いていなければ新規作成
- スタックが存在すれば構成を更新（zipアップロード + 変数更新）

**実装の要点**:
- `Session`モデルに`rm_stack_id: str | None`フィールドを追加
- スタック作成時: `CreateZipUploadConfigSourceDetails`で構成をアップロード
- スタック更新時: `UpdateZipUploadConfigSourceDetails`で構成を更新
- `compartment_id`はセッションの`export_iac`時点ではなく、RM API呼び出し時に必要
  → `variables`引数から取得するか、環境変数`GALLEY_WORK_COMPARTMENT_ID`から取得
- `terraform_version = "1.5.x"`を指定
- RM自動入力変数（`region`, `compartment_ocid`, `tenancy_ocid`）はvariablesから除外してRMに任せる

### 4. ジョブ実行 (`_run_rm_job`)

**責務**:
- Plan/Apply/Destroyジョブを作成
- 完了までポーリング
- ログを取得してTerraformResult形式に変換

**実装の要点**:
- `create_job` + `get_job`ポーリング（`CompositeOperations`にはバグがあるため手動ポーリング）
- ポーリング間隔: 5秒、タイムアウト: plan 5分、apply/destroy 30分
- ジョブログは`get_job_logs`で取得し、stdoutに相当する文字列として返却
- `SUCCEEDED`→`success=True`、`FAILED`→`success=False`でTerraformResultを構築
- plan_summaryはログから正規表現で抽出（既存の`_extract_plan_summary`を再利用）

### 5. IaCテンプレート変更 (`design.py`)

**責務**:
- 生成するTerraformテンプレートをRM互換にする

**変更点**:
- `variable "compartment_id"` → `variable "compartment_ocid"`（RM自動入力対応）
- `variable "tenancy_ocid"` を追加（RM自動入力、空定義のみ）
- providerブロック: `region = var.region` のみ（auth行を削除、RM環境判定コードも削除）
- components.tf内の`var.compartment_id`参照 → `var.compartment_ocid`に変更
- `_TF_RESOURCE_TEMPLATES`内のすべてのテンプレートで`compartment_id`参照を更新

### 6. ツールインターフェース変更 (`tools/infra.py`)

**変更点**:
- `run_terraform_plan/apply/destroy`: ツールの引数・返却値は変更なし（内部のみRM経由に）
- `terraform_dir`引数は引き続き受け取るが、RM実行時はzip化の対象パスとして使用
- `variables`引数: RM自動入力分（region, compartment_ocid）は内部で除外
- `create_rm_stack`, `run_rm_plan`, `run_rm_apply`: `run_terraform_*`がRM経由になるため、これらの独立ツールは削除
- `get_rm_job_status`: 実装して残す（ジョブの進行状況確認用）
- `update_terraform_file`: 維持（ローカルファイル編集 → 次回plan時にzipアップロード）

## データフロー

### Plan実行
```
1. LLMが run_terraform_plan(session_id, terraform_dir, variables) を呼び出し
2. InfraService: terraform_dirのファイルをzip化
3. InfraService: セッションのrm_stack_idを確認
   - なければ create_stack（zip, variables）→ stack_idをセッションに保存
   - あれば update_stack（zip, variables）
4. InfraService: create_job(stack_id, operation=PLAN)
5. InfraService: get_jobでポーリング → SUCCEEDED/FAILED
6. InfraService: get_job_logsでログ取得
7. InfraService: ログからplan_summaryを抽出
8. TerraformResult形式で返却
```

### Apply実行
```
1. LLMが run_terraform_apply(session_id, terraform_dir, variables) を呼び出し
2. InfraService: terraform_dirのファイルをzip化
3. InfraService: update_stack（変更があれば）
4. InfraService: create_job(stack_id, operation=APPLY, execution_plan_strategy=AUTO_APPROVED)
5. ポーリング → ログ取得 → TerraformResult返却
```

### Destroy実行
```
1. LLMが run_terraform_destroy(session_id, terraform_dir, variables) を呼び出し
2. InfraService: create_job(stack_id, operation=DESTROY, execution_plan_strategy=AUTO_APPROVED)
3. ポーリング → ログ取得 → TerraformResult返却
```

## エラーハンドリング戦略

### 新しいエラークラス

```python
class RMStackCreationError(GalleyError):
    """RMスタック作成に失敗した場合。"""

class RMJobError(GalleyError):
    """RMジョブが失敗した場合。"""
```

### エラーハンドリングパターン

- OCI SDK例外 → キャッチしてTerraformResult(success=False)で返却（LLMがデバッグできるよう）
- ポーリングタイムアウト → TerraformResult(success=False, stderr="Job timed out")
- スタック作成失敗 → TerraformResult(success=False, stderr=error_message)

## テスト戦略

### ユニットテスト
- RMクライアント初期化（ResourcePrincipal / API Key）
- zip化処理（ファイル包含/除外）
- RM自動入力変数の除外
- `compartment_id` → `compartment_ocid` のリネーム
- providerブロックのauth行なし
- ジョブポーリングのモック
- ログからplan_summary抽出

### 統合テスト（mcp-gauge E2E）
- Hearing → Design → Export → Plan → Apply → Destroy のフルフロー
- `update_terraform_file`不要でplan成功

## 依存ライブラリ

`oci` パッケージは既にoci-cliの依存として含まれているため、追加インストール不要。

## ディレクトリ構造

```
src/galley/
  models/
    infra.py        # TerraformResult維持、RMStack/RMJob更新
    session.py      # rm_stack_idフィールド追加
  services/
    design.py       # IaCテンプレート変更（compartment_ocid, auth削除）
    infra.py        # RM経由実行への全面書き換え
  tools/
    infra.py        # 不要ツール削除、docstring更新
```

## 実装の順序

1. **モデル変更**: Session.rm_stack_id追加、infra.pyモデル更新
2. **design.py変更**: テンプレートのRM互換化
3. **infra.py書き換え**: RMクライアント、zip化、スタック管理、ジョブ実行
4. **tools/infra.py更新**: 不要ツール削除、docstring更新
5. **テスト更新**: 既存テスト修正 + 新テスト追加
6. **品質チェック**: ruff, mypy, 全テスト通過

## セキュリティ考慮事項

- RMスタックのvariablesにsensitive値（パスワード等）が含まれる場合、RMのis_terraform_input_sensitive機能を利用
- zip化時にtfstateや.terraformディレクトリを除外し、機密情報の漏洩を防止

## パフォーマンス考慮事項

- RMジョブの起動には10-30秒のオーバーヘッドがある（ローカル実行よりは遅い）
- ポーリング間隔5秒で応答性と負荷のバランスを取る
- RMクライアントは遅延初期化してインスタンス化コストを回避
