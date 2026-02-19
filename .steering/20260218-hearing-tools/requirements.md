# 要求内容

## 概要

ヒアリング質問定義・フロー定義へのアクセスを、MCPリソースからMCPツールに変更し、Claude Desktopから確実に利用できるようにする。

## 背景

Claude DesktopでGalleyのPromptsを利用してヒアリングを開始したところ、「ヒアリング質問のリソースに直接アクセスできない」というメッセージが表示された。

原因は、`start_hearing` プロンプトが `galley://hearing/questions` リソースの参照を指示しているが、Claude DesktopはMCPリソースの自動読み取りをサポートしていないため。MCPツールは完全にサポートされているため、ツールとして公開することで解決する。

## 実装対象の機能

### 1. ヒアリング質問・フロー取得ツールの追加
- `get_hearing_questions` ツール: `config/hearing-questions.yaml` の内容をツール経由で返却
- `get_hearing_flow` ツール: `config/hearing-flow.yaml` の内容をツール経由で返却

### 2. プロンプトの参照先変更
- `start_hearing` プロンプト: リソース参照（`galley://hearing/questions`）をツール呼び出し（`get_hearing_questions`）に変更
- `resume_hearing` プロンプト: 同様にリソースからツールに変更

## 受け入れ条件

### ツール追加
- [x] `get_hearing_questions` ツールが質問定義をYAMLパース済みdictで返す
- [x] `get_hearing_flow` ツールがフロー定義をYAMLパース済みdictで返す
- [x] ツール総数が15→17に増加する

### プロンプト修正
- [x] `start_hearing` プロンプトがリソースではなくツールを参照する
- [x] `resume_hearing` プロンプトがリソースではなくツールを参照する

### 回帰テスト
- [x] 既存の全テスト（unit + integration）がパスする
- [x] リモートエンドポイントで17ツールが返却される

### Claude Desktop動作確認
- [x] Claude Desktopからヒアリング開始時に「リソースにアクセスできない」エラーが出ない

## 成功指標

- Claude Desktopで `start_hearing` プロンプトを使用した際、質問定義を正常に取得してヒアリングを進行できる

## スコープ外

以下はこのフェーズでは実装しない:

- 既存リソース（`galley://hearing/questions`, `galley://hearing/flow`）の削除（他クライアント向けに維持）
- 設計層リソースのツール化（現時点でClaude Desktopから問題報告なし）

## 参照ドキュメント

- `.steering/20260218-deploy-fixes/` - デプロイ修正タスク（Claude Desktop接続対応）
- `docs/architecture.md` - アーキテクチャ設計書
