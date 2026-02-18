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

- [x] Architecture, Component, Connection モデルを作成（models/architecture.py）
- [x] ValidationResult, ValidationRule モデルを作成（models/validation.py）
- [x] Session モデルに architecture フィールドを追加（models/session.py）
- [x] 新しいエラークラスを追加（models/errors.py）
  - [x] ArchitectureNotFoundError
  - [x] ComponentNotFoundError

## フェーズ2: 設定ファイル

- [x] OCIサービス定義ファイルを作成（config/oci-services.yaml）
- [x] バリデーションルールディレクトリと接続要件ルールを作成（config/validation-rules/connection-requirements.yaml）

## フェーズ3: バリデーター

- [x] validators/__init__.py を作成
- [x] ArchitectureValidator を実装（validators/architecture.py）

## フェーズ4: サービス層

- [x] DesignService を実装（services/design.py）
  - [x] save_architecture メソッド
  - [x] add_component メソッド
  - [x] remove_component メソッド
  - [x] configure_component メソッド
  - [x] validate_architecture メソッド
  - [x] list_available_services メソッド
  - [x] export_summary メソッド
  - [x] export_mermaid メソッド
  - [x] export_iac メソッド
  - [x] export_all メソッド

## フェーズ5: MCPインターフェース

- [x] 設計系MCPツールを実装（tools/design.py）
- [x] エクスポート系MCPツールを実装（tools/export.py）
- [x] 設計関連MCPリソースを実装（resources/design.py）
- [x] 設計支援MCPプロンプトを実装（prompts/design.py）
- [x] server.py に設計層の登録を追加

## フェーズ6: テスト

- [x] Architectureモデルのユニットテスト（tests/unit/models/test_architecture.py）
- [x] ArchitectureValidatorのユニットテスト（tests/unit/validators/test_architecture.py）
- [x] DesignServiceのユニットテスト（tests/unit/services/test_design.py）
- [x] 設計フローの統合テスト（tests/integration/test_design_flow.py）
- [x] conftest.py に設計系フィクスチャを追加

## フェーズ7: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `uv run pytest` — 87 passed
- [x] リントエラーがないことを確認
  - [x] `uv run ruff check .` — All checks passed
- [x] 型エラーがないことを確認
  - [x] `uv run mypy src/` — Success: no issues found in 26 source files
- [x] フォーマットが適用されていることを確認
  - [x] `uv run ruff format --check .` — 42 files already formatted

---

## 実装後の振り返り

### 実装完了日
2026-02-18

### 計画と実績の差分

**計画と異なった点**:
- `DesignService.__init__` のシグネチャが機能設計書と異なる: スペックでは `(storage, validator)` だが、実装では `(storage, config_dir)` とした。`config_dir` を渡して内部でValidatorを生成する方がシンプルで依存が少ない。
- `ArchitectureValidator` がStorageServiceではなくconfig_dirを直接参照: 本番環境でのObject Storage経由読み込みは将来のタスク。現フェーズではローカルファイル読み込みで十分。
- `export_iac` はTerraformスケルトン（コメント）のみ生成: 完全なTerraformコード生成はLLM側の責務。GalleyはLLMが参考にできる構造情報を提供する役割。

**新たに必要になったタスク**:
- なし。計画通りに実装完了。

**技術的理由でスキップしたタスク**:
- なし。全タスク完了。

### 学んだこと

**技術的な学び**:
- FastMCPの `@mcp.tool()` / `@mcp.resource()` / `@mcp.prompt()` デコレータパターンが非常に一貫しており、新しいドメイン層の追加が容易だった
- Pydanticの `model_dump()` / `model_validate()` によるJSONシリアライゼーションが、テストでのアサーションやストレージ永続化で自然に使える
- `Architecture.validation_results` を `list[Any]` として扱い `model_dump()` 結果を格納するトレードオフ: 型安全性は低下するが、永続化時のデシリアライゼーション問題を回避できる

**プロセス上の改善点**:
- フェーズ分割（データモデル→設定→バリデーター→サービス→MCP→テスト→品質チェック）が依存関係の順序と一致しており、各フェーズが独立してコンパイル・テスト可能だった
- 既存のHearingService実装パターンを踏襲したことで、設計の一貫性を保ちつつ迅速に実装できた

### 次回への改善提案
- Phase 4（インフラ層）では外部プロセス実行（Terraform、OCI CLI）が入るため、モック戦略をより厳密に設計する必要がある
- `ArchitectureValidator` のObject Storage移行時は、非同期メソッドへの変更が必要になるため、インターフェースを先に定義してから実装する方が良い
- `add_component` での `service_type` バリデーション（oci-services.yamlとの照合）は将来追加を検討する
