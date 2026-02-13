# Galley MCP Server

プリセールスエンジニア向けのOCIアーキテクチャ設計支援MCPサーバーです。

対話型ヒアリングで案件要件を構造化し、OCIサービスを使ったアーキテクチャ設計・成果物出力（要件サマリー、構成図、IaCテンプレート）までをLLMと連携して実行します。

## 目次

- [前提条件](#前提条件)
- [インストール](#インストール)
- [MCPクライアントへの接続設定](#mcpクライアントへの接続設定)
  - [Claude Desktop](#claude-desktop)
  - [Claude Code](#claude-code)
  - [その他のMCPクライアント](#その他のmcpクライアント)
- [基本的な使い方](#基本的な使い方)
- [提供機能の一覧](#提供機能の一覧)
  - [Tools（12種）](#tools12種)
  - [Resources（8種）](#resources8種)
  - [Prompts（3種）](#prompts3種)
- [データの保存先](#データの保存先)
- [設定のカスタマイズ](#設定のカスタマイズ)
  - [CLIオプション](#cliオプション)
  - [設定ファイルの上書き](#設定ファイルの上書き)
- [開発者向け情報](#開発者向け情報)

## 前提条件

- **Node.js 22** 以上
- MCPクライアント（Claude Desktop、Claude Code、Cline など）

## インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd Galley

# 依存パッケージのインストール
npm install

# ビルド
npm run build
```

ビルドが完了すると `dist/index.js` が生成されます。これがMCPサーバーの実行ファイルです。

## MCPクライアントへの接続設定

Galleyは [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) の標準的なStdio Transportで通信します。お使いのMCPクライアントにサーバーを登録してください。

### Claude Desktop

`claude_desktop_config.json`（macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`）に以下を追加します。

```json
{
  "mcpServers": {
    "galley": {
      "command": "node",
      "args": ["/path/to/Galley/dist/index.js"]
    }
  }
}
```

`/path/to/Galley` はクローンしたディレクトリの絶対パスに置き換えてください。

### Claude Code

プロジェクトルートの `.mcp.json` に追加するか、グローバル設定ファイル `~/.claude/mcp.json` に追加します。

```json
{
  "mcpServers": {
    "galley": {
      "command": "node",
      "args": ["/path/to/Galley/dist/index.js"]
    }
  }
}
```

### その他のMCPクライアント

Galleyは標準的なStdio Transportを使用しているため、MCP対応のあらゆるクライアントから利用できます。基本的な起動コマンドは以下のとおりです。

```bash
node /path/to/Galley/dist/index.js
```

オプションを指定する場合:

```bash
node /path/to/Galley/dist/index.js --data-dir /custom/data/dir --log-level debug
```

## 基本的な使い方

MCPクライアントを起動し、Galleyサーバーが接続されていることを確認したら、以下の流れで利用できます。

### 1. ヒアリングの開始

MCPクライアントのプロンプト機能から **start-hearing** を選択し、案件の概要を入力します。

```
案件概要: 在庫管理システムをOCI上にクラウドネイティブ化する案件のデモ環境を構築したい
```

LLMが選択式の質問を通じて、規模・トラフィック・データベース・ネットワーク・セキュリティ・可用性などの要件を段階的にヒアリングします。

- 各質問には番号付きの選択肢が表示されます
- 「わからない」を選ぶと、LLMが根拠付きで推測値を提案します
- 回答は自動的にセッションに保存されます

### 2. アーキテクチャの生成

ヒアリング完了後、プロンプト機能から **generate-architecture** を選択します。

LLMがヒアリング結果とOCIサービスカタログを参照して、以下を生成します。

- 要件サマリー（確定 ✅ / 推測 🔶 / 未確認 ⚠️ の区分付き）
- OCIコンポーネントの選定と理由
- Mermaid記法の構成図
- Terraform形式のIaCテンプレート
- アンチパターン検出に基づく警告

### 3. 成果物の出力

生成された成果物はファイルとしてエクスポートされます。

```
~/.galley/output/<session_id>/
  summary.md             # 要件サマリー（Markdown）
  architecture.mmd       # 構成図（Mermaid）
  terraform/
    main.tf              # IaCテンプレート
    variables.tf
    ...
```

### ヒアリングの中断と再開

ヒアリングを途中で中断しても、セッションは保存されています。再開するにはプロンプト機能から **resume-hearing** を選択し、セッションIDを指定してください。

## 提供機能の一覧

### Tools（12種）

#### ヒアリング関連

| ツール名 | 説明 |
|---------|------|
| `create_session` | 新しいヒアリングセッションを作成します |
| `save_answer` | ヒアリングの回答を1件保存します |
| `save_answers_batch` | ヒアリングの回答を一括保存します |
| `complete_hearing` | ヒアリングを完了し、要件の充足状況サマリーを返します |
| `get_hearing_result` | ヒアリング結果（全回答）を取得します |
| `list_sessions` | セッション一覧を取得します（ステータスでフィルタ可能） |
| `delete_session` | セッションと関連する出力ファイルを削除します |

#### 生成・出力関連

| ツール名 | 説明 |
|---------|------|
| `save_architecture` | アーキテクチャ設計結果をセッションに保存します |
| `export_summary` | 要件サマリーをMarkdownファイルとして出力します |
| `export_mermaid` | 構成図をMermaidファイル（`.mmd`）として出力します |
| `export_iac` | IaCテンプレートをTerraformファイルとして出力します |
| `export_all` | 上記の全成果物を一括出力します |

### Resources（8種）

MCPのResources機能を通じて、LLMがコンテキストとして参照するデータを提供します。

| リソースURI | 説明 |
|------------|------|
| `galley://templates/hearing-questions` | ヒアリング質問テンプレート（10カテゴリ） |
| `galley://templates/hearing-flow` | ヒアリングフロー定義（質問順序・条件分岐） |
| `galley://schemas/hearing-result` | ヒアリング結果のJSON Schema |
| `galley://sessions` | セッション一覧 |
| `galley://sessions/{session_id}` | セッション詳細（ヒアリング結果含む） |
| `galley://references/oci-services` | OCIサービスカタログ（20サービス） |
| `galley://references/oci-architectures` | OCIリファレンスアーキテクチャ（6パターン） |
| `galley://references/oci-terraform` | OCI Terraformリソース定義（10リソース） |

### Prompts（3種）

MCPのPrompts機能を通じて、LLMの動作を制御するプロンプトテンプレートを提供します。

| プロンプト名 | 引数 | 説明 |
|-------------|------|------|
| `start-hearing` | `project_description` | 新規ヒアリングを開始するプロンプト |
| `resume-hearing` | `session_id` | 中断したヒアリングを再開するプロンプト |
| `generate-architecture` | `session_id` | ヒアリング結果からアーキテクチャを生成するプロンプト |

## データの保存先

デフォルトでは `~/.galley/` にデータが保存されます。

```
~/.galley/
  sessions/
    <session_id>/
      session.json           # セッションメタデータ
      hearing-result.json    # ヒアリング結果
      architecture.json      # アーキテクチャ設計結果
  output/
    <session_id>/
      summary.md             # 要件サマリー
      architecture.mmd       # Mermaid構成図
      terraform/             # IaCテンプレート
        main.tf
        ...
```

`--data-dir` オプションで保存先を変更できます。

## 設定のカスタマイズ

### CLIオプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--data-dir` | `~/.galley` | セッションデータと出力ファイルの保存先 |
| `--config-dir` | なし | 設定ファイルのオーバーライドディレクトリ |
| `--log-level` | `info` | ログレベル（`debug` / `info` / `warning` / `error`） |

MCP設定ファイルの `args` に追加する例:

```json
{
  "mcpServers": {
    "galley": {
      "command": "node",
      "args": [
        "/path/to/Galley/dist/index.js",
        "--data-dir", "/custom/data/dir",
        "--log-level", "debug"
      ]
    }
  }
}
```

### 設定ファイルの上書き

Galleyの動作を制御する設定ファイルは3つのレイヤーで管理されており、優先度の高い順に読み込まれます。

1. **オーバーライド**（`--config-dir` で指定したディレクトリ）
2. **ユーザー設定**（`~/.galley/config/`）
3. **デフォルト**（パッケージ同梱の `config/`）

たとえばヒアリングの質問カテゴリをカスタマイズしたい場合は、`~/.galley/config/hearing-questions.yaml` にファイルを配置してください。同名のファイルがあれば、デフォルトの代わりにそちらが読み込まれます。

カスタマイズ可能な設定ファイル:

| ファイル名 | 説明 |
|-----------|------|
| `hearing-questions.yaml` | ヒアリング質問のカテゴリ定義 |
| `hearing-flow.yaml` | ヒアリングの質問順序と条件分岐ルール |
| `oci-services.yaml` | OCIサービスカタログ |
| `oci-architectures.yaml` | リファレンスアーキテクチャのパターン定義 |
| `oci-terraform.yaml` | Terraformリソースの定義と例 |

## 開発者向け情報

### 開発環境のセットアップ

```bash
npm install
```

### 主要コマンド

```bash
# ビルド
npm run build

# ウォッチモードでビルド（開発時）
npm run dev

# テスト実行
npm test

# テスト（ウォッチモード）
npm run test:watch

# 型チェック
npm run typecheck

# リント
npm run lint

# フォーマット
npm run format

# 全品質チェック（型チェック + リント + テスト + ビルド）
npm run check
```

### 技術スタック

| コンポーネント | 技術 |
|--------------|------|
| ランタイム | Node.js 22+ |
| 言語 | TypeScript 5.7+ (ESM) |
| MCP SDK | @modelcontextprotocol/sdk 1.12+ |
| バリデーション | Zod 3.24+ |
| 設定ファイル | YAML (yaml パッケージ) |
| バンドラー | tsup |
| テスト | Vitest |
| リンター | ESLint 9 + typescript-eslint |
| フォーマッター | Prettier |

### プロジェクト構造

```
src/
  index.ts              # CLIエントリーポイント
  server.ts             # MCPサーバー組み立て
  core/
    config.ts           # 設定ファイルローダー（3層マージ）
    errors.ts           # エラーハンドリング
    logger.ts           # ロガー（stderr + MCP logging）
    schema.ts           # Zodスキーマ定義
    storage.ts          # ファイルI/O抽象（アトミック書き込み）
  types/
    hearing.ts          # ヒアリング結果の型
    session.ts          # セッションの型
    architecture.ts     # アーキテクチャ出力の型
    index.ts            # バレルエクスポート
  hearing/
    resources.ts        # ヒアリング関連リソース（5種）
    tools.ts            # ヒアリング関連ツール（7種）
    prompts.ts          # ヒアリング関連プロンプト（2種）
  generate/
    resources.ts        # 生成関連リソース（3種）
    tools.ts            # 生成関連ツール（5種）
    prompts.ts          # 生成関連プロンプト（1種）
config/                 # デフォルト設定ファイル
prompts/                # プロンプトテンプレート
tests/                  # テスト（ユニット + 統合）
```

### ライセンス

未定
