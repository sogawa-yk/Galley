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

## フェーズ1: プロジェクト基盤の構築

- [x] pyproject.tomlを作成する（依存関係、ツール設定を含む）
- [x] .python-versionを作成する
- [x] パッケージディレクトリ構造を作成する（src/galley/ 以下の__init__.py群）
- [x] テストディレクトリ構造を作成する（tests/ 以下の__init__.py群）
- [x] `uv sync` で依存関係をインストールする

## フェーズ2: データモデルの実装

- [x] models/errors.py — カスタム例外クラスを実装する
- [x] models/session.py — Session、Answer、HearingResult、Requirementモデルを実装する

## フェーズ3: 設定管理とストレージの実装

- [x] config.py — ServerConfig設定クラスを実装する
- [x] config/hearing-questions.yaml — ヒアリング質問定義を作成する
- [x] config/hearing-flow.yaml — ヒアリングフロー定義を作成する
- [x] storage/service.py — StorageService（ローカルファイルシステム版）を実装する

## フェーズ4: ヒアリングサービスの実装

- [x] services/hearing.py — HearingServiceを実装する
  - [x] create_session メソッド
  - [x] save_answer メソッド
  - [x] save_answers_batch メソッド
  - [x] complete_hearing メソッド
  - [x] get_hearing_result メソッド

## フェーズ5: MCPインターフェースの実装

- [x] tools/hearing.py — ヒアリングMCPツールを実装する
  - [x] create_session ツール
  - [x] save_answer ツール
  - [x] save_answers_batch ツール
  - [x] complete_hearing ツール
  - [x] get_hearing_result ツール
- [x] resources/hearing.py — ヒアリングMCPリソースを実装する
- [x] prompts/hearing.py — ヒアリングMCPプロンプトを実装する

## フェーズ6: サーバーエントリポイントの実装

- [x] server.py — GalleyServerの実装（FastMCPインスタンス作成、ツール/リソース/プロンプト登録）
- [x] __main__.py — コマンドラインエントリポイントの実装

## フェーズ7: テストの実装

- [x] tests/conftest.py — 共通フィクスチャを作成する
- [x] tests/unit/models/test_session.py — データモデルのユニットテスト
- [x] tests/unit/storage/test_service.py — StorageServiceのユニットテスト
- [x] tests/unit/services/test_hearing.py — HearingServiceのユニットテスト
- [x] tests/integration/test_hearing_flow.py — MCPプロトコル経由の統合テスト

## フェーズ8: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `uv run pytest` — 39 passed
- [x] リントエラーがないことを確認
  - [x] `uv run ruff check .` — All checks passed
- [x] 型エラーがないことを確認
  - [x] `uv run mypy src/` — Success: no issues found in 17 source files
- [x] フォーマットが適用されていることを確認
  - [x] `uv run ruff format --check .` — 28 files already formatted

---

## 実装後の振り返り

### 実装完了日
2026-02-17

### 計画と実績の差分

**計画と異なった点**:
- `pyproject.toml` のビルドバックエンド設定が `hatchling.backends` ではなく `hatchling.build` であった。初回の `uv sync` でエラーとなり修正。
- FastMCP 2.x の `Client.call_tool()` が `CallToolResult` オブジェクトを返す仕様であり、統合テストで `result[0].text` のようにリスト添字でアクセスするコードが動作しなかった。`result.content[0].text` に修正。
- `pydantic-settings` が `pydantic` とは別パッケージであることを見落としていた。`pyproject.toml` の `dependencies` に追加が必要だった。
- `config.py` のデフォルトパスが相対パスで、実行ディレクトリ依存の問題があった。パッケージルートからの絶対パスに変更。
- `hearing-questions.yaml` の `purpose` 質問カテゴリが `general` であり、`_build_hearing_result` で `requirements` にも `constraints` にも分類されない問題があった。`other` に修正。

**新たに必要になったタスク**:
- implementation-validator サブエージェントによる品質検証後の修正作業（上記5点）

**技術的理由でスキップしたタスク**: なし

### 学んだこと

**技術的な学び**:
- FastMCP 2.x の `Client` API: `call_tool()` は `CallToolResult` を返し、`content` 属性でコンテンツブロックのリストにアクセスする
- `pydantic-settings` は `pydantic` とは独立したパッケージ。`BaseSettings` を使う場合は明示的に依存関係に追加が必要
- Pythonパッケージの `__main__.py` でモジュールレベルに副作用のあるコードを書くと、importだけで実行されてしまう。`if __name__ == "__main__":` ブロック内に閉じ込めるべき
- `hatchling` のビルドバックエンドは `hatchling.build` であり、`hatchling.backends` ではない

**プロセス上の改善点**:
- tasklist.md をフェーズごとに更新する運用が効果的だった
- implementation-validator による検証で、依存関係の漏れやパス問題など自分では見落としていた問題が検出できた

### 次回への改善提案
- 依存関係は実装と同時に `pyproject.toml` に追加し、`uv sync` で確認する習慣を持つ
- デフォルトパスは最初から絶対パスで設計する（相対パスは実行ディレクトリ依存のバグの温床）
- 設定ファイル（YAML）のカテゴリ値と、コード内の条件分岐が整合しているか、実装時に確認する
- FastMCPなど外部ライブラリのAPIは、テスト実装前に実際の戻り値型を確認する
