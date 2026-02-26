# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

---

## フェーズ1: データモデルとエラークラス

- [x] models/app.py を作成（TemplateMetadata, TemplateParameter, DeployResult, AppStatus）
- [x] models/errors.py にエラークラスを追加（TemplateNotFoundError, ProtectedFileError, AppNotScaffoldedError）

## フェーズ2: サービス層

- [x] services/app.py を作成（AppService クラス）
  - [x] list_templates: config/templates/ からテンプレートメタデータ読み込み
  - [x] scaffold_from_template: テンプレートからプロジェクト生成
  - [x] update_app_code: アプリコード更新（protected_paths保護、スナップショット保存）
  - [x] build_and_deploy: スタブ実装
  - [x] check_app_status: 状態取得

## フェーズ3: MCPインターフェース

- [x] tools/app.py を作成（register_app_tools）
- [x] prompts/app.py を作成（register_app_prompts）
- [x] server.py にAppService/ツール/プロンプトの登録を追加

## フェーズ4: サンプルテンプレート

- [x] config/templates/rest-api-adb/ にサンプルテンプレートを作成
  - [x] template.json（メタデータ定義）
  - [x] app/ ディレクトリ（テンプレートファイル）

## フェーズ5: テスト

- [x] tests/unit/models/test_app.py を作成
- [x] tests/unit/services/test_app.py を作成
- [x] tests/integration/test_app_flow.py を作成
- [x] tests/conftest.py に app_service fixture を追加

## フェーズ6: 品質チェックと修正

- [x] `uv run pytest` で全テスト通過（180テスト全通過）
- [x] `uv run ruff check .` でリントエラーなし
- [x] `uv run mypy src/` で型エラーなし（既存ファイルの既知エラーのみ、新規コードにエラーなし）

## フェーズ7: コンテナイメージのビルドとプッシュ

- [x] `docker build` でコンテナイメージをビルド
- [x] `preview` タグでOCIRにプッシュ

---

## 実装後の振り返り

### 実装完了日
2026-02-19

### 計画と実績の差分

**計画と異なった点**:
- テンプレートメタデータ（protected_paths等）をセッションディレクトリに保存する設計を追加。scaffold時にtemplate-metadata.jsonを保存し、update_app_code時に参照する方式とした
- pyproject.tomlに`extend-exclude = ["config/templates"]`を追加。テンプレートファイル（Galleyソースコードではない）がruffチェック対象から外れるようにした

**新たに必要になったタスク**:
- テンプレートファイルのruff除外設定（pyproject.toml修正）

### 学んだこと

**技術的な学び**:
- FastMCPのClient経由統合テストでは、既存のセッション前提条件（ヒアリング完了＋アーキテクチャ設定済み）をMCPツール呼び出しで再現するヘルパー関数が必要
- fnmatchによるprotected_paths照合は、ワイルドカードパターン（`src/*.py`等）にも対応できる柔軟な仕組み
- `_validate_file_path`でパストラバーサル防止は「..」パターン検出で実装したが、ファイル名に「..」を含む正当なケースでは誤検出の可能性がある（現時点では許容範囲）

**プロセス上の改善点**:
- 既存パターン（infra層のtools/services/models構成）に忠実に従うことで、実装速度と一貫性の両立ができた
- テストを先に設計してから実装する方が効率的だったかもしれない

### 次回への改善提案
- build_and_deployのスタブを実OCI DevOps/OKE連携に置き換える際は、非同期ジョブ管理とステータスポーリングの設計が必要
- check_app_statusの重複returnを実装時に解消する（現在はスタブのため同一値を返している）
- `_validate_file_path`のパストラバーサル検出をPurePathベースに改善することを検討
