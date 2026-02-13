# 初回実装 要求定義書（Requirements）

## 1. 目的

Galley MCPサーバーのMVP（Phase 1: 個人利用MVP）を実装する。プリセールスエンジニアが自身のAIクライアント（Claude Desktop等）から、ヒアリング→アーキテクチャ設計→アウトプット生成のコアフローを一気通貫で実行できる状態を構築する。

---

## 2. スコープ

### 2.1 対象ユーザーストーリー

プロダクト要求定義書（product-requirements.md）で定義されたMVP対象ユーザーストーリーのうち、以下を実装する。

| # | ユーザーストーリー | 優先度 | 実装順 |
|---|-------------------|--------|--------|
| US1 | 選択式ヒアリング：案件概要を伝えると、選択式の質問で要件を具体化する | Must | 1 |
| US2 | 推測による補完：「わからない」に対して根拠付きの推測値を提示する | Must | 2 |
| US4 | アーキテクチャ自動生成：ヒアリング結果からOCIアーキテクチャを生成する | Must | 3 |
| US5 | 要件サマリー：確定/推測/未確認を区別した要件サマリーを出力する | Must | 4 |
| US3 | 推測の根拠表示：推測根拠の信頼度を確認できる | Should | 5 |
| US6 | 構成図生成：Mermaid記法でアーキテクチャ構成図を出力する | Should | 6 |
| US7 | IaCテンプレート生成：Terraform形式のIaCテンプレートを出力する | Could | 7 |

### 2.2 実装対象のMCPプリミティブ

#### Resources（8個）

| URI | 説明 | モジュール |
|-----|------|-----------|
| `galley://templates/hearing-questions` | 質問カテゴリテンプレート | hearing |
| `galley://templates/hearing-flow` | ヒアリングフロー進行ルール | hearing |
| `galley://schemas/hearing-result` | ヒアリング結果JSONスキーマ | hearing |
| `galley://sessions` | セッション一覧 | hearing |
| `galley://sessions/{session_id}` | セッション詳細 | hearing |
| `galley://references/oci-services` | OCIサービスカタログ | generate |
| `galley://references/oci-architectures` | OCIリファレンスアーキテクチャ集 | generate |
| `galley://references/oci-terraform` | OCI Terraform Providerリソース一覧 | generate |

#### Tools（12個）

| ツール名 | 説明 | モジュール |
|---------|------|-----------|
| `create_session` | 新規セッション作成 | hearing |
| `save_answer` | 回答保存（1件） | hearing |
| `save_answers_batch` | 回答一括保存 | hearing |
| `complete_hearing` | ヒアリング完了 | hearing |
| `get_hearing_result` | ヒアリング結果取得 | hearing |
| `list_sessions` | セッション一覧取得 | hearing |
| `delete_session` | セッション削除 | hearing |
| `save_architecture` | アーキテクチャ設計保存 | generate |
| `export_summary` | 要件サマリーMarkdown出力 | generate |
| `export_mermaid` | 構成図Mermaidファイル出力 | generate |
| `export_iac` | IaCテンプレートファイル出力 | generate |
| `export_all` | 全成果物一括出力 | generate |

#### Prompts（3個）

| プロンプト名 | 説明 | モジュール |
|-------------|------|-----------|
| `start-hearing` | ヒアリング開始 | hearing |
| `resume-hearing` | ヒアリング再開 | hearing |
| `generate-architecture` | アーキテクチャ生成 | generate |

### 2.3 開発コンテナ（Dev Container）

開発環境の再現性を確保するため、Dev Container定義を作成する。

#### 要件

| 項目 | 内容 |
|------|------|
| ベースイメージ | Node.js 22（LTS） |
| Claude Code CLI | コンテナ内にインストールし、ターミナルから `claude` コマンドが使用可能 |
| パッケージマネージャ | npm |
| VS Code拡張機能 | ESLint、Prettier、Mermaid Preview等をプリインストール |
| 初期化 | コンテナ作成時に `npm install` を自動実行 |
| API キー | ホスト側の `ANTHROPIC_API_KEY` 環境変数をコンテナに引き継ぐ |

#### 成果物

```
.devcontainer/
├── devcontainer.json          ... Dev Container設定（機能・拡張機能・環境変数・ライフサイクルフック）
└── Dockerfile                 ... カスタムDockerfile（Claude Code CLIインストール等、必要な場合のみ）
```

> **判断基準**: Dev Container Featuresだけで要件を満たせる場合はDockerfileを作成しない。Claude Code CLIのインストールがFeaturesで対応できない場合にのみDockerfileを用意する。

### 2.4 実装対象外

- 社内実績（`internal_record`）による推測根拠（チーム展開段階）
- 共有ナレッジストア連携
- デモ環境の自動構築
- CI/CDパイプライン
- npm公開（パッケージとしての公開は別作業）

---

## 3. 受け入れ条件

### 3.1 コアフロー

- [ ] AIクライアントから `start-hearing` プロンプトを呼び出し、ヒアリングを開始できる
- [ ] `create_session` で新規セッションが作成され、`~/.galley/sessions/{session_id}/` にファイルが生成される
- [ ] 10カテゴリの質問テンプレート（Resources）がAIクライアントに提供される
- [ ] `save_answer` / `save_answers_batch` で回答が保存される
- [ ] 「わからない」回答に対して、推測値・根拠・信頼度ラベル（`public_reference` / `general_estimate`）が保存される
- [ ] `complete_hearing` でセッションステータスが `completed` に更新される
- [ ] `get_hearing_result` でヒアリング結果JSONが取得できる
- [ ] `save_architecture` でアーキテクチャ設計結果が保存される
- [ ] `export_summary` / `export_mermaid` / `export_iac` / `export_all` で成果物がファイル出力される
- [ ] 中断したヒアリングを `resume-hearing` プロンプトで再開できる

### 3.2 データ永続性

- [ ] セッションデータがJSON形式で `~/.galley/sessions/` に保存される
- [ ] ファイル書き込みはアトミック操作（一時ファイル→rename）で行われる
- [ ] MCPサーバー再起動後も前回のセッションデータが参照可能

### 3.3 設定ファイル

- [ ] `config/` 内の5つのYAMLファイルがデフォルト設定として読み込まれる
- [ ] `~/.galley/config/` にカスタム設定を配置するとデフォルトを上書きする
- [ ] `--config-dir` オプションで設定ディレクトリを指定できる

### 3.4 CLIオプション

- [ ] `--data-dir` でデータディレクトリを変更できる
- [ ] `--config-dir` で設定ディレクトリを変更できる
- [ ] `--log-level` でログレベルを変更できる（debug / info / warning / error）

### 3.5 エラーハンドリング

- [ ] 存在しないセッションIDへのアクセスで適切なエラーメッセージが返される
- [ ] ファイル書き込み失敗時に具体的な原因を含むエラーが返される
- [ ] Tool引数のバリデーションエラー時にフィールド名を含むエラーが返される
- [ ] パストラバーサル攻撃が防止される
- [ ] すべてのToolハンドラが `wrapToolHandler` で共通エラー処理される

### 3.6 開発コンテナ

- [ ] VS Codeの「Reopen in Container」でDev Containerが起動する
- [ ] コンテナ内で `node --version` が v22.x を返す
- [ ] コンテナ内で `claude --version` が実行でき、Claude Code CLIが使用可能
- [ ] コンテナ起動時に `npm install` が自動実行され、依存パッケージがインストール済み
- [ ] ホスト側の `ANTHROPIC_API_KEY` がコンテナ内で参照可能
- [ ] ESLint、Prettier等の推奨拡張機能が自動インストールされる
- [ ] コンテナ内で `npm run build`、`npm run test`、`npm run lint` が正常に実行できる

### 3.7 品質

- [ ] `npm run typecheck` が成功する（TypeScript strict mode）
- [ ] `npm run lint` が成功する
- [ ] `npm run test` で全テストが通過する
- [ ] テストカバレッジ: core モジュール 80%以上
- [ ] `npm run build` でビルドが成功する
- [ ] MCP Inspectorで全Resources/Tools/Promptsの動作確認が完了する

---

## 4. 制約事項

### 4.1 技術制約

- Node.js >= 22（LTS）
- TypeScript 5.x（strict mode）
- ESM（`"type": "module"`）
- `@modelcontextprotocol/sdk` ^1.x
- `console.log()` 使用禁止（stdioプロトコル破壊防止）
- 外部ネットワーク通信なし

### 4.2 設計制約

- 単一MCPサーバーとして実装（galley-hearing / galley-generateは内部モジュール）
- `hearing/` と `generate/` の相互依存禁止
- `core/` は上位モジュールに依存しない
- 共有データは `core/storage.ts` 経由のファイルI/Oで受け渡す
- 名前付きエクスポートのみ（`export default` 禁止）
- インポートパスに `.js` 拡張子を含める

### 4.3 パフォーマンス制約

- Tool応答時間: 各操作 < 500ms（export_all以外は < 100ms）
- Resourceサイズ合計: < 23 KB（~7,500 tokens）
- セッション一覧取得: 100セッションまで < 200ms

### 4.4 セキュリティ制約

- `~/.galley/` のパーミッション: 700
- ファイル出力先は `{data-dir}/output/{session_id}/` 配下に限定
- エラーメッセージに絶対パスを含めない
- ユーザー入力（Tool引数）はZodでバリデーション

---

## 5. 成果物

初回実装完了時に以下が揃っている状態を目指す。

| 成果物 | 説明 |
|--------|------|
| ソースコード（`src/`） | 全モジュール（hearing/generate/core/types）の実装 |
| 設定ファイル（`config/`） | 5つのYAMLファイル（質問テンプレート、フロー定義、OCIリファレンス3種） |
| プロンプトテンプレート（`prompts/`） | 3つのMarkdownファイル |
| テストコード（`tests/`） | ユニットテスト（core 80%以上カバレッジ） |
| ビルド設定 | `package.json`、`tsconfig.json`、`tsup.config.ts`、`vitest.config.ts`、`eslint.config.js`、`.prettierrc` |
| 開発環境 | `.vscode/`（extensions.json、settings.json）、`.gitignore` |
| 開発コンテナ | `.devcontainer/`（devcontainer.json、必要に応じてDockerfile） |
