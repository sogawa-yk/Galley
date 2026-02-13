# 初回実装 タスクリスト（Tasklist）

## 概要

design.md の Phase 0〜7 に基づく実装タスク一覧。各タスクは「1コミット1変更」の粒度で定義する。
各フェーズ完了時にビルド・テストが通る状態を維持する。

**総ファイル数**: 約 42 ファイル
**フェーズ数**: 8（Phase 0〜7）

---

## Phase 0: 環境セットアップ

### P0-1: Dev Container定義の作成

- [x]`.devcontainer/devcontainer.json` を作成
  - ベースイメージ: `mcr.microsoft.com/devcontainers/typescript-node:22`
  - `postCreateCommand`: `npm install -g @anthropic-ai/claude-code && npm install`
  - `remoteEnv`: `ANTHROPIC_API_KEY` をホストから引き継ぎ
  - VS Code拡張機能: ESLint、Prettier、Mermaid Preview
  - エディタ設定: formatOnSave、ESLint autofix

**受け入れ条件**: 3.6（開発コンテナ）

### P0-2: プロジェクト初期化

- [x]`package.json` を作成
  - `name`: `galley-mcp`、`version`: `0.1.0`、`type`: `module`
  - `bin`、`files`、`scripts`、`engines`、`dependencies`、`devDependencies` をdesign.md §2.2通りに定義
- [x]`tsconfig.json` を作成（strict mode、Node16モジュール）
- [x]`tsup.config.ts` を作成（ESM、shebang、external設定）
- [x]`vitest.config.ts` を作成（カバレッジ設定含む）
- [x]`eslint.config.js` を作成（フラットコンフィグ、console.log禁止、recommendedTypeChecked）
- [x]`.prettierrc` を作成
- [x]`.gitignore` を作成
- [x]`.vscode/extensions.json` を作成
- [x]`.vscode/settings.json` を作成
- [x]`npm install` を実行し、`package-lock.json` を生成

**受け入れ条件**: 3.7（品質 — ビルド設定が正常動作すること）

### P0-3: ソースディレクトリの骨格作成

- [x]`src/index.ts` — 最小限のエントリポイント（空のmain関数）
- [x]`src/server.ts` — スタブ
- [x]`src/core/` — 空ファイルまたはスタブ（errors.ts、logger.ts、storage.ts、config.ts、schema.ts）
- [x]`src/types/` — 空ファイルまたはスタブ（hearing.ts、session.ts、architecture.ts、index.ts）
- [x]`src/hearing/` — 空ファイルまたはスタブ（resources.ts、tools.ts、prompts.ts）
- [x]`src/generate/` — 空ファイルまたはスタブ（resources.ts、tools.ts、prompts.ts）
- [x]`npm run typecheck` が成功することを確認
- [x]`npm run build` が成功することを確認

**完了条件**: ディレクトリ構造がrepository-structure.mdと一致し、typecheck・buildが通る

---

## Phase 1: 共通基盤（core/）

### P1-1: errors.ts の実装

- [x]`GalleyErrorCode` 型を定義（8種類のエラーコード）
- [x]`GalleyError` クラスを実装（code、message、cause）
- [x]`wrapToolHandler` 関数を実装（Logger引数、GalleyError→isError変換、予期しないエラー→Internal server error）
- [x]`tests/core/errors.test.ts` を作成
  - GalleyError の生成テスト
  - wrapToolHandler: 正常系、GalleyError発生時、予期しないエラー発生時

### P1-2: logger.ts の実装

- [x]`LogLevel` 型を定義（debug / info / warning / error）
- [x]`Logger` インターフェースを定義（debug / info / warning / error / setServer）
- [x]`createLogger` ファクトリ関数を実装
  - ログレベルフィルタリング
  - stderr出力（`console.error()`）
  - MCP出力（`server.sendLoggingMessage()`）— server設定前はstderrのみ
- [x]`tests/core/logger.test.ts` を作成（任意 — loggerはシンプルなため優先度低）

### P1-3: storage.ts の実装

- [x]`StorageOptions` インターフェースを定義
- [x]`Storage` インターフェースを定義（design.md §3.3のメソッド一覧）
- [x]`createStorage` ファクトリ関数を実装
  - `initDataDir()`: `~/.galley/sessions/`、`~/.galley/output/` の自動作成（mode: 0o700）
  - `readJson<T>()` / `writeJson()`: JSON読み書き
  - `readText()` / `writeText()`: テキスト読み書き
  - `writeJson` / `writeText` のアトミック書き込み（tmpファイル → rename）
  - `validatePath()`: パストラバーサル防止（`path.resolve()` + baseDirプレフィックスチェック）
  - `validateFilename()`: `..`、`/`、`\` を含む名前の拒否
  - `listDirs()`: ディレクトリ一覧取得
  - `removeDir()`: ディレクトリ削除
  - Node.js `ENOENT`、`EACCES` 等の `GalleyError` への変換
- [x]`tests/core/storage.test.ts` を作成（実ファイルシステム使用）
  - `beforeEach` でos.tmpdir()配下に一時ディレクトリ作成
  - `afterEach` でクリーンアップ
  - アトミック書き込みのテスト
  - パストラバーサル防止のテスト
  - ディレクトリ初期化のテスト
  - 存在しないファイルのエラーテスト
  - ファイル名バリデーションのテスト

**受け入れ条件**: 3.2（データ永続性）、3.5（エラーハンドリング — パストラバーサル防止）

### P1-4: config.ts の実装

- [x]`ConfigLoaderOptions` インターフェースを定義
- [x]`ConfigLoader` インターフェースを定義（loadConfig、loadPromptTemplate、getResolvedConfigDir）
- [x]`createConfigLoader` ファクトリ関数を実装
  - 3段階マージ: overrideConfigDir → userConfigDir → defaultConfigDir
  - YAML読み込み（`yaml` パッケージ使用）
  - Zodスキーマバリデーション
  - プロンプトテンプレート読み込み（Markdownファイル）
- [x]`renderTemplate` 関数をモジュールレベルでエクスポート
  - `{{variable_name}}` の文字列置換
- [x]`tests/core/config.test.ts` を作成
  - 3段階マージのテスト（デフォルトのみ / ユーザー上書き / CLI上書き）
  - 不正YAMLのエラーテスト
  - ファイル不在のエラーテスト
  - `renderTemplate` のテスト（単一変数 / 複数変数 / 未定義変数）
  - Zodバリデーション失敗のテスト

**受け入れ条件**: 3.3（設定ファイル）

### P1-5: schema.ts の実装

- [x]データモデルスキーマの定義
  - `EstimationSchema`、`AnsweredItemSchema`
  - `SessionSchema`
  - `HearingResultSchema`（requirements の各フィールドはoptional）
  - `ComponentSchema`、`WarningSchema`、`ArchitectureOutputSchema`
- [x]Tool引数スキーマの定義
  - `CreateSessionArgsSchema`
  - `SaveAnswerArgsSchema`、`SaveAnswersBatchArgsSchema`
  - `SessionIdArgsSchema`、`ListSessionsArgsSchema`
  - `SaveArchitectureArgsSchema`
  - `ExportMermaidArgsSchema`、`ExportIacArgsSchema`
  - `ExportAllArgsSchema`（mermaid_code / iac_files はoptional）
- [x]設定ファイルスキーマの定義
  - `HearingQuestionsConfigSchema`
  - `HearingFlowConfigSchema`
  - `OciServicesConfigSchema`
  - `OciArchitecturesConfigSchema`
  - `OciTerraformConfigSchema`
- [x]`tests/core/schema.test.ts` を作成
  - 各スキーマの正常系バリデーション
  - 各スキーマの異常系バリデーション（必須フィールド欠落、型不一致）
  - HearingResultSchema の部分データ（途中セッション）のバリデーション

**受け入れ条件**: 3.5（エラーハンドリング — バリデーションエラー）

### P1-6: Phase 1 品質チェック

- [x]`npm run typecheck` 成功
- [x]`npm run lint` 成功
- [x]`npm run test` 全パス
- [x]`npm run build` 成功
- [x]core モジュールのカバレッジ 80%以上を確認

---

## Phase 2: 型定義（types/）

### P2-1: 型定義ファイルの作成

- [x]`src/types/hearing.ts` — `z.infer` で Estimation、AnsweredItem、HearingResult、ConfidenceLabel、AnswerSource を導出
- [x]`src/types/session.ts` — Session、SessionStatus を導出。SessionSummary インターフェースを手動定義
- [x]`src/types/architecture.ts` — ArchitectureOutput、Component、Warning を導出
- [x]`src/types/index.ts` — 全型を re-export（バレルファイル）
- [x]`npm run typecheck` 成功を確認

**完了条件**: 全型が schema.ts の Zodスキーマから導出され、typecheckが通る

---

## Phase 3: 設定ファイル + プロンプトテンプレート

### P3-1: ヒアリング設定ファイルの作成

- [x]`config/hearing-questions.yaml` — 10カテゴリの質問定義（< 3 KB）
- [x]`config/hearing-flow.yaml` — 進行順序 + 条件分岐ルール（< 2 KB）
- [x]`config/hearing-result-schema.json` — HearingResult の JSON Schema（functional-design.md §3.1ベース）

### P3-2: OCI設定ファイルの作成

- [x]`config/oci-services.yaml` — OCI主要20サービスカタログ（< 8 KB）
- [x]`config/oci-architectures.yaml` — リファレンスアーキテクチャパターン（< 5 KB）
- [x]`config/oci-terraform.yaml` — Terraform Providerリソース定義（< 5 KB）
- [x]全設定ファイルの合計サイズが < 23 KB であることを確認

### P3-3: プロンプトテンプレートの作成

- [x]`prompts/start-hearing.md` — ヒアリング開始プロンプト（`{{project_description}}` 変数）
  - ヒアリングアシスタントの役割定義
  - 進行ルール（選択式 → 補足 → 推測のフロー）
  - 出力形式（save_answer の呼び出し方）
- [x]`prompts/resume-hearing.md` — ヒアリング再開プロンプト（`{{session_id}}` 変数）
  - get_hearing_result で現状取得
  - 未回答カテゴリから質問再開
- [x]`prompts/generate-architecture.md` — アーキテクチャ生成プロンプト（`{{session_id}}` 変数）
  - アーキテクチャ設計ルール
  - OCIサービス選定基準
  - アンチパターン検出
  - 出力形式（save_architecture の呼び出し方）

### P3-4: テストフィクスチャの作成

- [x]`tests/fixtures/sessions/test-session/session.json` — 正常なセッションデータ
- [x]`tests/fixtures/sessions/test-session/hearing-result.json` — ヒアリング途中データ
- [x]`tests/fixtures/sessions/test-session/hearing-result-complete.json` — ヒアリング完了データ
- [x]`tests/fixtures/sessions/test-session/architecture.json` — アーキテクチャデータ
- [x]`tests/fixtures/config/hearing-questions.yaml` — テスト用の質問テンプレート
- [x]`tests/fixtures/config/hearing-flow.yaml` — テスト用のフロー定義
- [x]`tests/fixtures/config/invalid.yaml` — 不正YAML（異常系テスト用）
- [x]`tests/fixtures/invalid/traversal-paths.json` — パストラバーサルテストケース
- [x]`tests/fixtures/invalid/malformed-session.json` — スキーマ不正のセッションデータ

### P3-5: Phase 3 品質チェック

- [x]設定ファイルがZodスキーマでバリデーション通過（config.test.ts で確認）
- [x]`npm run build` 成功

---

## Phase 4: ヒアリングモジュール（hearing/）

### P4-1: hearing/resources.ts の実装

- [x]`registerHearingResources` 関数を実装
- [x]`galley://templates/hearing-questions` — hearing-questions.yaml をJSON文字列として返す
- [x]`galley://templates/hearing-flow` — hearing-flow.yaml をJSON文字列として返す
- [x]`galley://schemas/hearing-result` — hearing-result-schema.json を返す
- [x]`galley://sessions` — セッション一覧を返す（storage.listDirs + 各session.json読み込み）
- [x]`galley://sessions/{session_id}` — リソーステンプレート。session.json + hearing-result.json を返す
- [x]テンプレートResourceの初回読み込みキャッシュ
- [x]`tests/hearing/resources.test.ts` を作成

### P4-2: hearing/tools.ts の実装（セッション管理）

- [x]`registerHearingTools` 関数を実装
- [x]`create_session` — セッション作成（UUID生成、session.json + hearing-result.json の初期化、ResourcesListChanged通知）
- [x]`list_sessions` — セッション一覧取得（statusフィルタリング、created_at降順ソート）
- [x]`delete_session` — セッション削除（sessions/ + output/ 削除、ResourcesListChanged通知）
- [x]全ハンドラを `wrapToolHandler` でラップ
- [x]`tests/hearing/tools.test.ts` にセッション管理テストを作成
  - create_session: 正常系、バリデーションエラー
  - list_sessions: フィルタリング、空一覧
  - delete_session: 正常系、存在しないセッション

### P4-3: hearing/tools.ts の実装（回答保存・完了）

- [x]`save_answer` — 回答保存（1件）
  - status確認（in_progress のみ許可）
  - category → requirements フィールドマッピング
  - hearing-result.json アトミック書き込み
  - session.json の updated_at 更新
- [x]`save_answers_batch` — 回答一括保存
  - 1回の読み込み → 全回答適用 → 1回の書き込み
- [x]`complete_hearing` — ヒアリング完了
  - status が in_progress であること確認（completed ならエラー）
  - hearing-result.json の metadata.status を completed に更新
  - session.json の status を completed に更新
  - 回答サマリー（回答済み/未回答カテゴリ数）を返却
- [x]`get_hearing_result` — ヒアリング結果取得
  - HearingResultSchema でバリデーション
- [x]テスト追加
  - save_answer: 正常系、completed セッションへの書き込みエラー、不正カテゴリ
  - save_answers_batch: 正常系、部分的に不正な回答
  - complete_hearing: 正常系、二重完了エラー
  - get_hearing_result: 正常系、存在しないセッション

**受け入れ条件**: 3.1（コアフロー — セッション作成、回答保存、ヒアリング完了、結果取得）

### P4-4: hearing/prompts.ts の実装

- [x]`registerHearingPrompts` 関数を実装
- [x]`start-hearing` プロンプト — `project_description` 引数、renderTemplate で展開
- [x]`resume-hearing` プロンプト — `session_id` 引数、renderTemplate で展開
- [x]テスト（任意 — prompts は低優先度）

### P4-5: Phase 4 品質チェック

- [x]`npm run typecheck` 成功
- [x]`npm run lint` 成功
- [x]`npm run test` 全パス
- [x]`npm run build` 成功

---

## Phase 5: アウトプット生成モジュール（generate/）

### P5-1: generate/resources.ts の実装

- [x]`registerGenerateResources` 関数を実装
- [x]`galley://references/oci-services` — OciServicesConfigSchema でバリデーション、JSON文字列として返す
- [x]`galley://references/oci-architectures` — OciArchitecturesConfigSchema でバリデーション
- [x]`galley://references/oci-terraform` — OciTerraformConfigSchema でバリデーション
- [x]初回読み込みキャッシュ
- [x]`tests/generate/resources.test.ts` を作成

### P5-2: generate/tools.ts の実装（save_architecture + export_summary）

- [x]`registerGenerateTools` 関数を実装
- [x]`save_architecture` — アーキテクチャ設計保存
  - SaveArchitectureArgsSchema でバリデーション
  - セッション存在確認
  - architecture.json アトミック書き込み
- [x]`export_summary` — 要件サマリーMarkdown出力
  - hearing-result.json 読み込み
  - architecture.json 読み込み（存在する場合）
  - ✅ 確定事項 / 🔶 推測 / ⚠️ 未確認の分類
  - output/{session_id}/summary.md に出力
  - 相対パスを返却（絶対パス禁止）
- [x]全ハンドラを `wrapToolHandler` でラップ
- [x]テスト追加
  - save_architecture: 正常系、バリデーションエラー
  - export_summary: 正常系（全回答あり / 推測あり / 未回答あり）

### P5-3: generate/tools.ts の実装（export_mermaid + export_iac + export_all）

- [x]`export_mermaid` — 構成図Mermaidファイル出力
  - ExportMermaidArgsSchema でバリデーション
  - output/{session_id}/architecture.mmd に出力
- [x]`export_iac` — IaCテンプレートファイル出力
  - ExportIacArgsSchema でバリデーション
  - validateFilename() でファイル名チェック
  - output/{session_id}/terraform/{name} に出力
- [x]`export_all` — 全成果物一括出力
  - ExportAllArgsSchema でバリデーション
  - export_summary を常に実行
  - mermaid_code 指定時は export_mermaid を実行
  - iac_files 指定時は export_iac を実行
  - 出力ファイル一覧を返却
- [x]テスト追加
  - export_mermaid: 正常系
  - export_iac: 正常系、不正ファイル名
  - export_all: summaryのみ / summary + mermaid / 全出力

**受け入れ条件**: 3.1（コアフロー — 成果物のファイル出力）

### P5-4: generate/prompts.ts の実装

- [x]`registerGeneratePrompts` 関数を実装
- [x]`generate-architecture` プロンプト — `session_id` 引数、renderTemplate で展開
- [x]テスト（任意）

### P5-5: Phase 5 品質チェック

- [x]`npm run typecheck` 成功
- [x]`npm run lint` 成功
- [x]`npm run test` 全パス
- [x]`npm run build` 成功

---

## Phase 6: サーバー + エントリポイント

### P6-1: server.ts の実装

- [x]`ServerDependencies` インターフェースを定義
- [x]`createGalleyServer` 関数を実装
  - McpServer インスタンスの生成（capabilities: resources.listChanged、tools、prompts、logging）
  - hearing モジュールの登録（registerHearingResources、registerHearingTools、registerHearingPrompts）
  - generate モジュールの登録（registerGenerateResources、registerGenerateTools、registerGeneratePrompts）
- [x]MCP SDK の McpServer コンストラクタの実際のシグネチャを確認し、必要に応じて調整

### P6-2: index.ts の実装

- [x]CLI引数パース（`node:util` の `parseArgs` を使用）
  - `--data-dir`: デフォルト `~/.galley`
  - `--config-dir`: 設定ディレクトリ上書き
  - `--log-level`: デフォルト `info`
- [x]依存オブジェクトの初期化（logger → storage → configLoader → server）
- [x]パス解決（`import.meta.url` → PACKAGE_ROOT → config/、prompts/）
- [x]StdioServerTransport で MCP サーバー起動
- [x]エラーハンドリング（起動失敗時の `console.error` + `process.exit(1)`）

**受け入れ条件**: 3.4（CLIオプション）

### P6-3: Phase 6 品質チェック

- [x]`npm run typecheck` 成功
- [x]`npm run lint` 成功
- [x]`npm run test` 全パス
- [x]`npm run build` 成功
- [x]`node dist/index.js --help` または直接起動でエラーが出ないことを確認

---

## Phase 7: 統合テスト + 最終チェック

### P7-1: MCP Inspectorでの動作確認

- [x]`npm run inspect` でMCP Inspectorを起動
- [x]**Resources（8個）**の確認
  - [x]`galley://templates/hearing-questions` が質問カテゴリを返す
  - [x]`galley://templates/hearing-flow` がフロー定義を返す
  - [x]`galley://schemas/hearing-result` がJSON Schemaを返す
  - [x]`galley://sessions` がセッション一覧を返す（初期状態: 空）
  - [x]`galley://sessions/{session_id}` がセッション詳細を返す
  - [x]`galley://references/oci-services` がOCIサービスカタログを返す
  - [x]`galley://references/oci-architectures` がリファレンスアーキテクチャを返す
  - [x]`galley://references/oci-terraform` がTerraformリソース一覧を返す
- [x]**Tools（12個）**の確認
  - [x]`create_session` で新規セッションが作成される
  - [x]`save_answer` で回答が保存される
  - [x]`save_answers_batch` で一括回答が保存される
  - [x]`complete_hearing` でステータスが completed になる
  - [x]`get_hearing_result` でヒアリング結果が取得できる
  - [x]`list_sessions` でセッション一覧が取得できる
  - [x]`delete_session` でセッションが削除される
  - [x]`save_architecture` でアーキテクチャが保存される
  - [x]`export_summary` でsummary.mdが出力される
  - [x]`export_mermaid` でarchitecture.mmdが出力される
  - [x]`export_iac` でterraform/*.tfが出力される
  - [x]`export_all` で全成果物が一括出力される
- [x]**Prompts（3個）**の確認
  - [x]`start-hearing` がプロンプトテンプレートを返す
  - [x]`resume-hearing` がプロンプトテンプレートを返す
  - [x]`generate-architecture` がプロンプトテンプレートを返す

### P7-2: コアフローのE2Eテスト（手動）

- [x]フロー 1: ヒアリング → 完了
  1. `create_session` でセッション作成
  2. `save_answer` で数件の回答を保存
  3. `save_answers_batch` で複数回答を一括保存
  4. `complete_hearing` でヒアリング完了
  5. `get_hearing_result` で結果取得
  6. `~/.galley/sessions/{id}/` にファイルが正しく保存されていることを確認

- [x]フロー 2: アーキテクチャ生成 → 全出力
  1. 上記のセッションに対して `save_architecture` でアーキテクチャ保存
  2. `export_all` で summary + mermaid + iac を一括出力
  3. `~/.galley/output/{id}/` に全ファイルが出力されていることを確認

- [x]フロー 3: セッション再開
  1. 新しいセッションを作成、途中まで回答を保存
  2. MCP Inspectorを再起動（サーバー再起動をシミュレート）
  3. `list_sessions` で前回のセッションが一覧に表示される
  4. `get_hearing_result` で途中データが取得できる

- [x]フロー 4: エラーケース
  1. 存在しないセッションIDでのアクセス → エラーメッセージ確認
  2. completed セッションへの save_answer → INVALID_SESSION_STATUS エラー
  3. 不正なTool引数 → VALIDATION_ERROR + フィールド名表示

### P7-3: 最終品質チェック

- [x]`npm run typecheck` 成功
- [x]`npm run lint` 成功
- [x]`npm run test` 全パス
- [x]`npm run test:coverage` で core/ のカバレッジ 80%以上
- [x]`npm run build` 成功
- [x]`npm run format:check` 差分なし

**受け入れ条件**: 3.7（品質 — 全チェック項目）

---

## 実装順序サマリー

```
P0-1 → P0-2 → P0-3（環境セットアップ）
  ↓
P1-1 → P1-2 → P1-3 → P1-4 → P1-5 → P1-6（共通基盤）
  ↓
P2-1（型定義）    ※ P1完了後
P3-1〜P3-4（設定ファイル + テストフィクスチャ）  ※ P0完了後（P1と並行可能）
  ↓
P4-1 → P4-2 → P4-3 → P4-4 → P4-5（ヒアリングモジュール）  ※ P1, P2, P3 完了後
P5-1 → P5-2 → P5-3 → P5-4 → P5-5（生成モジュール）  ※ P1, P2, P3 完了後。P4と並行可能
  ↓
P6-1 → P6-2 → P6-3（サーバー + エントリポイント）  ※ P4, P5 完了後
  ↓
P7-1 → P7-2 → P7-3（統合テスト + 最終チェック）  ※ P6 完了後
```

**推奨**: Phase 1 を先に完了させ、Phase 2 と Phase 3 を並行実装した後、Phase 4 → Phase 5 → Phase 6 → Phase 7 の順で進める。
