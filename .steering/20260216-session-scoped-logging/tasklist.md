# タスクリスト: セッションスコープファイルログ

## タスク一覧

### 1. Storage層の変更
- [ ] `src/core/storage.ts`: `Storage` インターフェースに `appendText` を追加
- [ ] `src/core/storage.ts`: `createStorage` 内に `appendText` の実装を追加
- [ ] `tests/core/storage.test.ts`: `appendText` のテストを追加（追記・新規作成・ディレクトリ自動作成・パストラバーサル拒否）

### 2. Logger層の変更
- [ ] `src/core/logger.ts`: `Logger` インターフェースに `forSession` を追加
- [ ] `src/core/logger.ts`: `createLogger` 内に `forSession` の実装を追加
- [ ] `tests/core/logger.test.ts`: 新規作成（ファイル書き込み・追記・レベルフィルタ・stderr委譲・書き込み失敗の安全性）

### 3. ツールハンドラの更新
- [ ] `src/hearing/tools.ts`: `create_session`、`delete_session` のログをセッションスコープに切り替え
- [ ] `src/generate/tools.ts`: `save_architecture` のログをセッションスコープに切り替え
- [ ] `src/deploy/tools.ts`: `create_rm_stack`、`run_rm_plan`、`run_rm_apply`、`get_rm_job_status` のログをセッションスコープに切り替え

### 4. テストモックの更新
- [ ] `tests/core/errors.test.ts`: モックLoggerに `forSession` を追加
- [ ] `tests/core/oci-cli.test.ts`: モックLoggerに `forSession` を追加

### 5. 品質チェック
- [ ] `npm run check`（typecheck + lint + test + build）が成功すること

## 完了条件

- 全タスクにチェックが入っていること
- `npm run check` が成功すること
