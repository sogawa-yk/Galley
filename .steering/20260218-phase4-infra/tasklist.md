# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### 実装可能なタスクのみを計画
- 計画段階で「実装可能なタスク」のみをリストアップ
- 「将来やるかもしれないタスク」は含めない
- 「検討中のタスク」は含めない

### タスクスキップが許可される唯一のケース
以下の技術的理由に該当する場合のみスキップ可能:
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

### タスクが大きすぎる場合
- タスクを小さなサブタスクに分割
- 分割したサブタスクをこのファイルに追加
- サブタスクを1つずつ完了させる

---

## フェーズ1: データモデルとエラークラス

- [x] TerraformResult, CLIResult モデルを作成（models/infra.py）
- [x] RMStack, RMJob モデルを作成（models/infra.py）
- [x] ~~models/__init__.py にインフラモデルのエクスポートを追加~~（実装方針変更により不要: 既存のmodels/__init__.pyが空ファイルであり、各モジュールから直接importするパターンを踏襲）
- [x] インフラ系エラークラスを追加（models/errors.py）
  - [x] TerraformError
  - [x] OCICliError
  - [x] CommandNotAllowedError
  - [x] InfraOperationInProgressError

## フェーズ2: InfraService実装

- [x] InfraService基盤を作成（services/infra.py）
  - [x] __init__ メソッド（storage, config_dir, セッションロック管理）
  - [x] OCI CLIホワイトリスト定義
- [x] run_terraform_plan メソッドを実装
- [x] run_terraform_apply メソッドを実装
- [x] run_terraform_destroy メソッドを実装
- [x] run_oci_cli メソッドを実装（ホワイトリスト検証付き）
- [x] oci_sdk_call メソッドを実装（現フェーズではスタブ）
- [x] Resource Manager メソッド群をスタブ実装
  - [x] create_rm_stack
  - [x] run_rm_plan
  - [x] run_rm_apply
  - [x] get_rm_job_status
- [x] ~~services/__init__.py にInfraServiceのエクスポートを追加~~（実装方針変更により不要: 既存のservices/__init__.pyが空ファイルであり、直接importパターンを踏襲）

## フェーズ3: MCPインターフェース

- [x] インフラ系MCPツールを実装（tools/infra.py）
  - [x] run_terraform_plan ツール
  - [x] run_terraform_apply ツール
  - [x] run_terraform_destroy ツール
  - [x] run_oci_cli ツール
  - [x] oci_sdk_call ツール
  - [x] create_rm_stack ツール
  - [x] run_rm_plan ツール
  - [x] run_rm_apply ツール
  - [x] get_rm_job_status ツール
- [x] server.py にインフラ層の登録を追加

## フェーズ4: テスト

- [x] TerraformResult / CLIResult モデルのユニットテスト（tests/unit/models/test_infra.py）
- [x] InfraServiceのユニットテスト（tests/unit/services/test_infra.py）
  - [x] Terraform plan/apply/destroy テスト（subprocessモック）
  - [x] OCI CLI実行テスト（subprocessモック）
  - [x] コマンドホワイトリスト検証テスト
  - [x] 排他制御テスト
- [x] インフラフローの統合テスト（tests/integration/test_infra_flow.py）
- [x] conftest.py にインフラ系フィクスチャを追加

## フェーズ5: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `uv run pytest` — 137 passed（パストラバーサル検証テスト5件追加後）
- [x] リントエラーがないことを確認
  - [x] `uv run ruff check .` — All checks passed
- [x] 型エラーがないことを確認
  - [x] `uv run mypy src/` — 新規ファイル(3ファイル)はSuccess: no issues found。既存のmiddleware.py/tools/hearing.pyに事前のエラーあり（今回の変更とは無関係）
- [x] フォーマットが適用されていることを確認
  - [x] `uv run ruff format --check .` — 49 files already formatted

---

## 実装後の振り返り

### 実装完了日
2026-02-18

### 計画と実績の差分

**計画と異なった点**:
- `models/__init__.py` と `services/__init__.py` へのエクスポート追加は、既存パターン（空ファイル＋直接import）に合わせてスキップ。技術的に正しい判断。
- `_validate_terraform_dir()` パストラバーサル検証を追加。バリデータ（implementation-validator）の指摘を受けて、セキュリティ強化として実装。当初のtasklist.mdにはなかったが、インフラ操作のセキュリティ上必須。
- tools/infra.pyの例外ハンドリングに`ValueError`を追加。パス検証のValueErrorをMCPレスポンスとして構造化して返すため。

**新たに必要になったタスク**:
- `_validate_terraform_dir()` 関数の実装とテスト5件追加。サブプロセスにユーザー入力のパスを渡す箇所のセキュリティ対策として必要だった。

**技術的理由でスキップしたタスク**:
- `models/__init__.py` エクスポート追加 — 既存パターンが空__init__.pyで直接importのため不要
- `services/__init__.py` エクスポート追加 — 同上

### 学んだこと

**技術的な学び**:
- `asyncio.create_subprocess_exec`でシェルインジェクションを防ぎつつ非同期プロセス実行ができる。`shell=True`を避けることでセキュリティリスクを低減。
- `shlex.split()`でコマンド文字列を安全にトークン化し、ホワイトリストと組み合わせることで堅牢なコマンド検証が実現できる。
- セッション単位の`asyncio.Lock`による排他制御パターンは、辞書で動的にロックを管理することで簡潔に実装可能。
- `_run_subprocess`をモックすることで、実際の外部コマンド実行なしにTerraform/OCI CLIのフロー全体をテストできる。

**プロセス上の改善点**:
- 5フェーズ構成（モデル→サービス→ツール→テスト→品質）が依存関係に沿った自然な実装順序で効率的だった
- 既存パターン（tools/design.py, services/design.py）を先に調査することで、新規実装の方向性が明確になった
- implementation-validatorサブエージェントによるレビューでパストラバーサルの問題が発見され、品質向上に貢献した

### 次回への改善提案
- セキュリティ関連のバリデーション（パス検証、入力サニタイズ）は設計段階で明示的にタスク化しておくとよい
- Resource Manager統合（OCI SDK連携）を実装する際は、OCI SDK for Pythonのクライアント初期化パターンを先に調査してからスタブを置き換えること
- `_config_dir`は将来のTerraformテンプレート格納用に残してあるが、実際に使用する段階で初めて具体的な設計を行うこと
