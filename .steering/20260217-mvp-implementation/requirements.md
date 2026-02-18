# 要求内容

## 概要

GalleyプロジェクトのMVP（Phase 1）として、MCPサーバー基盤とヒアリングセッション管理機能を実装する。

## 背景

Galleyは現在ドキュメントのみで、ソースコードが存在しない。Pythonプロジェクトの基盤（pyproject.toml、パッケージ構造）から構築し、MVPとして動作するMCPサーバーを完成させる必要がある。

## 実装対象の機能

### 1. F1: MCPサーバー基盤

- Python + FastMCPによるMCPサーバーの実装
- SSE / StreamableHTTP対応のMCP通信
- サーバーの起動・停止
- ツール・リソース・プロンプトの登録基盤

### 2. F2: ヒアリングセッション管理

- `galley:create_session` でヒアリングセッションを作成
- `galley:save_answer` / `galley:save_answers_batch` で回答を保存
- `galley:complete_hearing` でヒアリングを完了し、結果を構造化
- `galley:get_hearing_result` でヒアリング結果を取得
- セッションデータの永続化（MVP段階ではローカルファイルシステム）

### 3. プロジェクト基盤

- pyproject.tomlによるプロジェクト設定
- Pythonパッケージ構造の構築
- 開発ツール（Ruff、mypy、pytest）の設定
- 設定ファイル（hearing-questions.yaml、hearing-flow.yaml）の作成

## 受け入れ条件

### F1: MCPサーバー基盤
- [ ] FastMCPベースのMCPサーバーが `uv run python -m galley.server` で起動できる
- [ ] MCPホストからツール一覧を取得できる
- [ ] 登録されたツールをMCPプロトコル経由で呼び出せる

### F2: ヒアリングセッション管理
- [ ] `galley:create_session` でセッションを作成し、session_idを取得できる
- [ ] `galley:save_answer` で回答を保存できる
- [ ] `galley:save_answers_batch` で複数回答を一括保存できる
- [ ] `galley:complete_hearing` でヒアリングを完了し、構造化結果を取得できる
- [ ] `galley:get_hearing_result` でヒアリング結果を取得できる
- [ ] セッションデータが永続化される

### プロジェクト基盤
- [ ] `uv run pytest` でテストが実行できる
- [ ] `uv run ruff check .` でリントエラーがない
- [ ] `uv run mypy src/` で型エラーがない

## 成功指標

- MCPサーバーが起動し、MCPプロトコル経由でヒアリングツールが動作する
- ユニットテストと統合テストがパスする
- コード品質チェック（lint、typecheck）がパスする

## スコープ外

以下はこのフェーズでは実装しません:

- OCI Object Storageへの永続化（ローカルファイルシステムで代替）
- OCI SDK / OCI CLI連携（OCIClientFactory）
- Dockerfileの作成
- 配布用Terraform（F3）
- 設計層（F4〜F7）
- インフラ層（F8〜F10）
- アプリケーション層（F11〜F12）
- Resource Principal認証

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/functional-design.md` - 機能設計書
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/repository-structure.md` - リポジトリ構造定義書
- `docs/development-guidelines.md` - 開発ガイドライン
