# 設計: セッションスコープファイルログ

## 実装アプローチ

3つのレイヤーに分けて変更する:

1. **Storage層** — ファイル追記メソッドの追加
2. **Logger層** — セッションスコープロガーの生成メソッドの追加
3. **Tool層** — 既存のログ呼び出しをセッションスコープロガーに切り替え

## 変更するコンポーネント

### 1. Storage: `appendText` メソッド追加

**ファイル:** `src/core/storage.ts`

既存の `writeText` はアトミック書き込み（一時ファイル＋rename）を行うため、追記用途には不適。
`fs.appendFile` を使った追記専用メソッドを追加する。

```typescript
// Storage インターフェースに追加
appendText(relativePath: string, content: string): Promise<void>;

// 実装
async appendText(relativePath: string, content: string): Promise<void> {
  const absolutePath = validatePath(relativePath);
  try {
    const dir = path.dirname(absolutePath);
    await fs.mkdir(dir, { recursive: true });
    await fs.appendFile(absolutePath, content, 'utf-8');
  } catch (error) {
    wrapFsError(error, 'write', relativePath);
  }
},
```

- `validatePath` でパストラバーサルを防止（既存パターン踏襲）
- `mkdir` でディレクトリ自動作成（ほとんどの場合すでに存在するが安全策）

### 2. Logger: `forSession` メソッド追加

**ファイル:** `src/core/logger.ts`

`Logger` インターフェースに `forSession` を追加し、セッションスコープの子ロガーを返す。

```typescript
// インターフェースに追加
forSession(sessionId: string, storage: Storage, toolName: string): Logger;
```

**子ロガーの動作:**

```
slog.info("message", data)
  ├─→ 親ロガーの log() を呼び出し → stderr + MCP sendLoggingMessage
  └─→ storage.appendText(`sessions/${sessionId}/galley.log`, jsonLine)
       └─→ .catch(() => {})  // 書き込み失敗はサイレント無視
```

- 子ロガーは親の `shouldLog` レベルフィルタを共有する
- `Storage` は型のみインポート（`import type`）で循環依存なし
- 書き込みは fire-and-forget（`.catch(() => {})`）でツール実行をブロックしない

**ログエントリ形式:**

```jsonl
{"timestamp":"2026-02-16T12:00:00.000Z","level":"info","tool":"create_rm_stack","message":"RM stack created: ocid1.xxx","data":{...}}
```

- `data` フィールドは値がある場合のみ含める

### 3. ツールハンドラの更新

既存のログ呼び出し箇所で、Zodパース後に `forSession` でセッションロガーを生成し切り替える。

**パターン:**
```typescript
// Before
const parsed = SomeSchema.parse(args);
// ... 処理 ...
logger.info('message');

// After
const parsed = SomeSchema.parse(args);
const slog = logger.forSession(parsed.session_id, storage, 'tool_name');
// ... 処理 ...
slog.info('message');
```

**変更対象:**

| ファイル | ツール | 行 |
|---------|--------|-----|
| `src/hearing/tools.ts` | `create_session` | 108 |
| `src/hearing/tools.ts` | `delete_session` | 164 |
| `src/generate/tools.ts` | `save_architecture` | 101 |
| `src/deploy/tools.ts` | `create_rm_stack` | 140 |
| `src/deploy/tools.ts` | `run_rm_plan` | 184 |
| `src/deploy/tools.ts` | `run_rm_apply` | 239 |
| `src/deploy/tools.ts` | `get_rm_job_status` | 290 |

## データ構造の変更

既存のデータ構造への変更なし。新規ファイルが追加されるのみ:

```
sessions/<session_id>/
  session.json
  hearing-result.json
  architecture.json
  deploy-state.json
  galley.log              ← 新規追加
```

## 影響範囲の分析

### 影響あり

| ファイル | 変更種別 |
|---------|---------|
| `src/core/storage.ts` | インターフェース＋実装に `appendText` 追加 |
| `src/core/logger.ts` | インターフェース＋実装に `forSession` 追加、`Storage` 型インポート |
| `src/hearing/tools.ts` | 既存ログ呼び出し2箇所を `slog` に変更 |
| `src/generate/tools.ts` | 既存ログ呼び出し1箇所を `slog` に変更 |
| `src/deploy/tools.ts` | 既存ログ呼び出し4箇所を `slog` に変更 |
| `tests/core/storage.test.ts` | `appendText` テスト追加 |
| `tests/core/logger.test.ts` | 新規作成（`forSession` テスト） |
| `tests/core/errors.test.ts` | モックLoggerに `forSession` 追加 |
| `tests/core/oci-cli.test.ts` | モックLoggerに `forSession` 追加 |

### 影響なし

- `src/core/errors.ts` — `wrapToolHandler` の変更不要
- `src/server.ts` — DI構造の変更不要
- `src/index.ts` — 起動処理の変更不要
- `tests/deploy/tools.test.ts` — `createLogger()` を直接使用（自動的に `forSession` を持つ）
- `tests/integration/mcp-server.test.ts` — 同上
- `docs/` — 永続ドキュメントへの影響なし
