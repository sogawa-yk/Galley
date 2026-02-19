# 設計書

## アーキテクチャ概要

既存のレイヤードアーキテクチャに従い、インフラ層のコンポーネントを追加する。
HearingService / DesignService と同じパターンで InfraService を実装する。

```
MCPプロトコル層 (tools/infra.py)
    ↓
サービス層 (services/infra.py)
    ↓
データアクセス層 (storage/service.py)  +  外部プロセス実行 (asyncio.subprocess)
```

## コンポーネント設計

### 1. データモデル (models/infra.py)

**責務**:
- Terraform実行結果、OCI CLI結果、Resource Manager関連の構造化データモデル

**実装の要点**:
- 既存のPydantic BaseModelパターンを踏襲
- TerraformResult, CLIResult, RMStack, RMJob の4モデル

### 2. エラークラス (models/errors.py 追加)

**責務**:
- インフラ操作固有のエラークラス

**実装の要点**:
- TerraformError: stderr, exit_code を保持
- OCICliError: command, stderr, exit_code を保持
- CommandNotAllowedError: ホワイトリスト検証違反
- RMStackNotFoundError: Resource Managerスタック不在

### 3. InfraService (services/infra.py)

**責務**:
- Terraformコマンドの実行（plan / apply / destroy）
- OCI CLIコマンドの実行（ホワイトリスト検証付き）
- OCI SDK API呼び出し（将来実装のスタブ）
- Resource Manager操作（将来実装のスタブ）
- セッション単位のTerraform実行排他制御

**実装の要点**:
- `asyncio.create_subprocess_exec` で外部プロセスを非同期実行
- Terraform作業ディレクトリはセッション単位で分離
- OCI CLIコマンドはホワイトリスト方式で検証（`oci` で始まるコマンドのみ許可、サブコマンドをホワイトリスト照合）
- Resource Manager関連メソッドは OCI SDK 依存のため、現フェーズではスタブ実装（NotImplementedError ではなく、構造化エラーを返す）
- セッション単位で重量操作の排他制御（asyncio.Lock）

**OCI CLIホワイトリスト**:
```python
ALLOWED_OCI_COMMANDS = {
    "iam", "compute", "network", "bv", "os", "db",
    "container-instances", "resource-manager", "dns",
    "oke", "apigateway", "functions", "events",
}
```

### 4. MCPツール (tools/infra.py)

**責務**:
- インフラ層MCPツールの登録

**実装の要点**:
- `register_infra_tools(mcp, infra_service)` パターン
- 全ツールで `try/except GalleyError` のエラーハンドリング
- Terraform系: run_terraform_plan, run_terraform_apply, run_terraform_destroy
- OCI系: run_oci_cli, oci_sdk_call
- RM系: create_rm_stack, run_rm_plan, run_rm_apply, get_rm_job_status

## データフロー

### Terraform plan/apply
```
1. MCPホスト → tools/infra.py: run_terraform_plan(session_id, terraform_dir)
2. tools/infra.py → InfraService.run_terraform_plan()
3. InfraService: セッション排他ロック取得
4. InfraService: asyncio.create_subprocess_exec("terraform", "plan", ...)
5. InfraService: stdout/stderr キャプチャ → TerraformResult 構築
6. InfraService: ロック解放
7. tools/infra.py → MCPホスト: TerraformResult JSON
```

### OCI CLI実行
```
1. MCPホスト → tools/infra.py: run_oci_cli(command)
2. tools/infra.py → InfraService.run_oci_cli()
3. InfraService: コマンドをホワイトリスト検証
4. InfraService: asyncio.create_subprocess_exec("oci", ...)
5. InfraService: stdout/stderr キャプチャ → CLIResult 構築
6. tools/infra.py → MCPホスト: CLIResult JSON
```

## エラーハンドリング戦略

### カスタムエラークラス

| エラー | 用途 |
|--------|------|
| TerraformError | Terraform実行失敗（exit_code != 0） |
| OCICliError | OCI CLI実行失敗 |
| CommandNotAllowedError | ホワイトリスト外のコマンド |
| RMStackNotFoundError | RMスタック不在 |
| InfraOperationInProgressError | 排他制御違反 |

### エラーハンドリングパターン

- Terraform実行エラー: TerraformResult(success=False) として構造化して返却（LLMが解析して自動修正するため、例外ではなく結果として返す）
- OCI CLIエラー: CLIResult(success=False) として返却
- ホワイトリスト違反: CommandNotAllowedError 例外を発生
- 排他制御違反: InfraOperationInProgressError 例外を発生

## テスト戦略

### ユニットテスト
- InfraService: Terraform plan/apply/destroy の各操作（subprocess モック）
- InfraService: OCI CLI実行（subprocess モック）
- InfraService: コマンドホワイトリスト検証
- InfraService: 排他制御（asyncio.Lock）
- TerraformResult / CLIResult モデルのバリデーション

### 統合テスト
- MCPプロトコル経由でのインフラツール呼び出し

## 依存ライブラリ

新規ライブラリの追加は不要。`asyncio.create_subprocess_exec` は標準ライブラリ。

## ディレクトリ構造

```
src/galley/
├── models/
│   ├── infra.py              # 新規: TerraformResult, CLIResult, RMStack, RMJob
│   └── errors.py             # 変更: インフラ系エラー追加
├── services/
│   └── infra.py              # 新規: InfraService
├── tools/
│   └── infra.py              # 新規: register_infra_tools
└── server.py                 # 変更: インフラ層登録追加

tests/
├── unit/
│   ├── models/
│   │   └── test_infra.py     # 新規
│   └── services/
│       └── test_infra.py     # 新規
└── integration/
    └── test_infra_flow.py    # 新規
```

## 実装の順序

1. データモデル（models/infra.py）
2. エラークラス追加（models/errors.py）
3. InfraService実装（services/infra.py）
4. MCPツール登録（tools/infra.py）
5. server.py にインフラ層を登録
6. ユニットテスト
7. 統合テスト
8. 品質チェック

## セキュリティ考慮事項

- OCI CLIコマンドのホワイトリスト検証: シェルインジェクション防止
- `asyncio.create_subprocess_exec` を使用（`shell=True` は使わない）
- Terraform作業ディレクトリのパストラバーサル防止
- セッションIDのサニタイズ（既存StorageServiceのパターンを踏襲）

## パフォーマンス考慮事項

- Terraform実行は非同期サブプロセスで実行し、メインスレッドをブロックしない
- セッション単位のasyncio.Lockで重量操作を逐次処理

## 将来の拡張性

- StorageServiceのObject Storage移行時に、Terraform state保存先も切り替え可能な設計
- OCIClientFactory導入時に、InfraServiceがSDK呼び出しを実装できるインターフェース設計
- Resource Manager操作のフル実装は OCI SDK 統合時に実施
