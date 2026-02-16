# 要求内容: セッションスコープファイルログ

## 概要

セッションディレクトリ（`sessions/<session_id>/`）にログファイルを配置し、各セッションに関連するツール操作の履歴をファイルとして永続化する。

## 背景

現在 Galley MCP サーバーのログは stderr と MCP `sendLoggingMessage` にのみ出力される。Stdio Transport 経由で通信するMCPサーバーでは stderr をユーザーが直接確認する手段がなく、セッションごとの操作履歴が追跡できない。

## ユーザーストーリー

- **運用担当者として**、特定のセッションで実行されたツール操作の履歴をファイルで確認したい。それにより、問題発生時のデバッグや操作の監査が可能になる。

## 機能要件

1. セッションに関連するツール呼び出し時に、`sessions/<session_id>/galley.log` にログを追記する
2. ログはJSON Lines（JSONL）形式で記録する
3. 各ログエントリに以下のフィールドを含める:
   - `timestamp` — ISO 8601形式のタイムスタンプ
   - `level` — ログレベル（debug / info / warning / error）
   - `tool` — 実行されたツール名
   - `message` — ログメッセージ
   - `data` — 付加データ（任意）
4. 既存のログ出力（stderr / MCP sendLoggingMessage）を維持する
5. セッションIDを持たないツール（`check_oci_cli`、`list_sessions`）はグローバルロガーのみを使用する
6. ログレベルフィルタは親ロガーの設定を引き継ぐ

## 非機能要件

- ログファイルへの書き込みエラーがツール実行を妨げてはならない（サイレントに無視）
- 既存のテストが壊れないこと（後方互換性）

## 受け入れ条件

- [ ] `sessions/<session_id>/galley.log` にJSON Lines形式でログが追記される
- [ ] 既存のstderr/MCPログ出力が引き続き動作する
- [ ] ログファイル書き込み失敗時にツールがエラーを返さない
- [ ] `npm run check`（typecheck + lint + test + build）が成功する

## 制約事項

- AsyncLocalStorage等の複雑なコンテキスト伝播は使用しない
- 既存のStorage/Loggerパターンを踏襲する
