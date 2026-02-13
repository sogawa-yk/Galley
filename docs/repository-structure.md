# リポジトリ構造定義書（Repository Structure）

## 1. 全体構成

### 1.1 リポジトリルート

```
galley/
├── src/                        ... アプリケーションソースコード
├── config/                     ... デフォルト設定ファイル（パッケージに同梱）
├── prompts/                    ... プロンプトテンプレート（.mdファイル）
├── tests/                      ... テストコード
├── docs/                       ... 永続的ドキュメント（設計・仕様）
├── .steering/                  ... 作業単位のステアリングファイル
├── .devcontainer/              ... Dev Container定義（開発環境コンテナ）
├── .vscode/                    ... VS Code推奨設定（共有対象）
├── package.json                ... npm パッケージ定義
├── tsconfig.json               ... TypeScript設定
├── tsup.config.ts              ... ビルド設定（tsup）
├── vitest.config.ts            ... テスト設定（Vitest）
├── eslint.config.js            ... ESLint設定（フラットコンフィグ）
├── .prettierrc                 ... Prettier設定
├── .gitignore                  ... Git除外設定
├── CLAUDE.md                   ... プロジェクトメモリ（Claude Code用）
├── README.md                   ... プロジェクト概要・セットアップ手順
└── LICENSE                     ... ライセンスファイル
```

### 1.2 ディレクトリの分類

| 分類 | ディレクトリ | npm パッケージに含むか | 説明 |
|------|------------|---------------------|------|
| ソースコード | `src/` | No（ビルド後の `dist/` を含む） | TypeScriptソースコード |
| ビルド成果物 | `dist/` | Yes（ソースマップを除く） | tsupによるビルド出力。gitignore対象 |
| 設定ファイル | `config/` | Yes | デフォルト設定（YAML）。パッケージに同梱 |
| プロンプト | `prompts/` | Yes | プロンプトテンプレート（.md）。パッケージに同梱 |
| テスト | `tests/` | No | ユニットテスト・テストフィクスチャ |
| ドキュメント | `docs/` | No | 設計・仕様ドキュメント |
| ステアリング | `.steering/` | No | 作業単位の一時ドキュメント |
| 開発コンテナ | `.devcontainer/` | No | Dev Container定義（Node.js 22 + Claude Code CLI） |
| エディタ設定 | `.vscode/` | No | VS Code推奨設定 |

---

## 2. ソースコード（`src/`）

### 2.1 ディレクトリ構成

```
src/
├── index.ts                    ... エントリポイント
├── server.ts                   ... MCPサーバー定義
│
├── hearing/                    ... ヒアリングモジュール
│   ├── resources.ts            ... Resources登録
│   ├── tools.ts                ... Tools登録
│   └── prompts.ts              ... Prompts登録
│
├── generate/                   ... アウトプット生成モジュール
│   ├── resources.ts            ... Resources登録
│   ├── tools.ts                ... Tools登録
│   └── prompts.ts              ... Prompts登録
│
├── core/                       ... 共通基盤
│   ├── storage.ts              ... ファイルI/O
│   ├── config.ts               ... 設定読み込み
│   ├── schema.ts               ... Zodスキーマ定義・バリデーション
│   ├── logger.ts               ... ログ出力
│   └── errors.ts               ... エラー定義
│
└── types/                      ... 共有型定義
    ├── hearing.ts              ... HearingResult, Answer, AnsweredItem等
    ├── session.ts              ... Session, SessionIndex等
    ├── architecture.ts         ... ArchitectureOutput, Component等
    └── index.ts                ... re-export
```

### 2.2 各ファイルの責務

#### エントリポイント

| ファイル | 責務 |
|---------|------|
| `index.ts` | CLI引数パース（`--data-dir`、`--config-dir`、`--log-level`）、MCPサーバーの起動、プロセスシグナルハンドリング |
| `server.ts` | MCPサーバーインスタンスの生成、各モジュール（hearing/generate/core）の登録、ケーパビリティ宣言 |

#### hearing モジュール

| ファイル | 責務 | 外部ファイル依存 |
|---------|------|----------------|
| `resources.ts` | セッション一覧・詳細、質問テンプレート、フロー定義のResource登録 | `config/hearing-questions.yaml`、`config/hearing-flow.yaml` |
| `tools.ts` | `create_session`、`save_answer`、`save_answers_batch`、`complete_hearing`、`get_hearing_result`、`list_sessions`、`delete_session` のTool登録。設定ファイル（質問テンプレート等）は直接参照せず、`core/storage.ts` 経由のファイルI/Oのみ | なし |
| `prompts.ts` | `start-hearing`、`resume-hearing` のPrompt登録。Markdownテンプレートの読み込みと変数展開 | `prompts/start-hearing.md`、`prompts/resume-hearing.md` |

#### generate モジュール

| ファイル | 責務 | 外部ファイル依存 |
|---------|------|----------------|
| `resources.ts` | OCIサービスカタログ、リファレンスアーキテクチャ、Terraformリソース一覧のResource登録 | `config/oci-services.yaml`、`config/oci-architectures.yaml`、`config/oci-terraform.yaml` |
| `tools.ts` | `save_architecture`、`export_summary`、`export_mermaid`、`export_iac`、`export_all` のTool登録。設定ファイルは直接参照せず、`core/storage.ts` 経由のファイルI/Oのみ | なし |
| `prompts.ts` | `generate-architecture` のPrompt登録。Markdownテンプレートの読み込みと変数展開 | `prompts/generate-architecture.md` |

#### core モジュール

| ファイル | 責務 |
|---------|------|
| `storage.ts` | ファイルの読み書き（アトミック書き込み）、パストラバーサル防止、`~/.galley/` ディレクトリの初期化 |
| `config.ts` | 設定ファイルの読み込み。3段階の優先順位マージ（CLI引数 > ユーザー設定 > デフォルト）。`config/` および `prompts/` のパス解決（後述 2.5参照） |
| `schema.ts` | Zodスキーマの定義とバリデーション関数。HearingResult、Session、ArchitectureOutput等の実行時検証 |
| `logger.ts` | ログ出力の抽象化。stderr（`console.error()`）と MCP sendLoggingMessage の使い分け |
| `errors.ts` | アプリケーション固有のエラークラス定義（`GalleyError`）。エラーコードとメッセージのマッピング |

#### types ディレクトリ

| ファイル | 定義する型 |
|---------|-----------|
| `hearing.ts` | `HearingResult`、`AnsweredItem`、`Estimation`、`ConfidenceLabel`、`AnswerSource` |
| `session.ts` | `Session`、`SessionStatus`、`SessionIndex` |
| `architecture.ts` | `ArchitectureOutput`、`Component`、`ComponentDecision`、`Warning` |
| `index.ts` | 上記すべての型を re-export |

> **バレルエクスポートについて**: `types/index.ts` は re-export のみのバレルファイルだが、CLIツール（単一エントリポイント）のためツリーシェイキングの影響はない。他モジュールからは `import { HearingResult } from '../types/index.js'` で参照する。

### 2.3 型定義の配置ルール

| 配置先 | 対象 | 例 |
|-------|------|-----|
| `src/types/` | 複数モジュールから参照される共有型 | `HearingResult`、`Session`、`ArchitectureOutput` |
| 各モジュールのファイル内 | そのモジュール内でのみ使う内部型 | Tool引数のZodスキーマ型、内部ヘルパー関数の引数型 |

**判断基準**: 2つ以上のモジュールが参照する型 → `src/types/`、1つのモジュール内で閉じる型 → そのファイル内にローカル定義。

### 2.4 モジュール間の依存関係

```
index.ts → server.ts → hearing/ → core/
                      → generate/ → core/

hearing/ ←✕→ generate/   （相互依存禁止）
core/    ←✕→ hearing/    （coreは上位モジュールに依存しない）
core/    ←✕→ generate/   （coreは上位モジュールに依存しない）
```

- `hearing/` と `generate/` は互いに直接参照しない。共有が必要なデータは `core/storage.ts` 経由でファイルシステムを介して受け渡す
- `core/` はどのモジュールにも依存しない（最下層）
- `types/` はどのモジュールからも参照可能（型定義のみ、ロジックを含まない）

### 2.5 パッケージ同梱ファイルのパス解決

`config/` と `prompts/` はビルド成果物（`dist/`）とは別ディレクトリに配置される。ランタイムで正しくパスを解決するため、以下の方針を採用する。

```
パッケージルート/
├── dist/index.js       ... エントリポイント（バンドル済み）
├── config/             ... デフォルト設定ファイル
└── prompts/            ... プロンプトテンプレート
```

**パス解決方法**:

```typescript
import { fileURLToPath } from 'node:url';
import path from 'node:path';

// dist/index.js からパッケージルートを算出
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PACKAGE_ROOT = path.resolve(__dirname, '..');

// パッケージ同梱ファイルへのパス
const DEFAULT_CONFIG_DIR = path.join(PACKAGE_ROOT, 'config');
const DEFAULT_PROMPTS_DIR = path.join(PACKAGE_ROOT, 'prompts');
```

- ESM（`"type": "module"`）を使用するため、`__dirname` は Node.js のグローバルとしては存在しない。`import.meta.url` から算出する
- `dist/index.js` → 1階層上がパッケージルート → `config/`、`prompts/` にアクセス
- `--config-dir` オプション指定時はこのデフォルトパスを上書きする

---

## 3. 設定ファイル（`config/`）

### 3.1 ディレクトリ構成

```
config/
├── hearing-questions.yaml      ... 質問カテゴリテンプレート
├── hearing-flow.yaml           ... ヒアリングフロー進行ルール
├── oci-services.yaml           ... OCIサービスカタログ（主要20サービス）
├── oci-architectures.yaml      ... OCIリファレンスアーキテクチャ集
└── oci-terraform.yaml          ... OCI Terraform Providerリソース一覧と使用例
```

### 3.2 各ファイルの役割

| ファイル | 内容 | サイズ目標 | 対応Resource URI | 参照元 |
|---------|------|----------|-----------------|--------|
| `hearing-questions.yaml` | 10カテゴリの質問定義（業種、規模、トラフィック等） | < 3 KB | `galley://templates/hearing-questions` | `src/hearing/resources.ts` |
| `hearing-flow.yaml` | ヒアリングの進行順序、分岐条件 | < 2 KB | `galley://templates/hearing-flow` | `src/hearing/resources.ts` |
| `oci-services.yaml` | OCI主要20サービスの名称・用途・制約・推奨構成 | < 8 KB | `galley://references/oci-services` | `src/generate/resources.ts` |
| `oci-architectures.yaml` | 業種・ユースケース別のリファレンスアーキテクチャパターン | < 5 KB | `galley://references/oci-architectures` | `src/generate/resources.ts` |
| `oci-terraform.yaml` | OCI Terraform Providerの主要リソース定義名と基本的な使用例 | < 5 KB | `galley://references/oci-terraform` | `src/generate/resources.ts` |

> **サイズ管理**: `config/` のファイルはMCP ResourcesとしてAIクライアントのコンテキストに読み込まれるため、トークン消費に直結する。合計 < 23 KB（~7,500 tokens）を目標とする。

### 3.3 配置ルール

- `config/` はパッケージに同梱されるデフォルト設定
- ユーザーがカスタマイズする場合は `~/.galley/config/` にファイルをコピーして編集する（ファイル単位で上書き）
- 設定ファイルのフォーマットはYAML。各ファイルに `version` フィールドを含める

---

## 4. プロンプトテンプレート（`prompts/`）

### 4.1 ディレクトリ構成

```
prompts/
├── start-hearing.md            ... ヒアリング開始プロンプト
├── resume-hearing.md           ... ヒアリング再開プロンプト
└── generate-architecture.md    ... アーキテクチャ生成プロンプト
```

### 4.2 各ファイルの役割

| ファイル | 内容 | 参照元 |
|---------|------|--------|
| `start-hearing.md` | ヒアリングアシスタントの役割定義、進行ルール、出力形式。`{{project_description}}` をテンプレート変数として含む | `src/hearing/prompts.ts` |
| `resume-hearing.md` | 中断セッションの再開手順。`{{session_id}}` をテンプレート変数として含む | `src/hearing/prompts.ts` |
| `generate-architecture.md` | アーキテクチャ設計ルール、出力形式定義。`{{session_id}}` をテンプレート変数として含む | `src/generate/prompts.ts` |

### 4.3 テンプレート変数の仕組み

- テンプレート変数は `{{variable_name}}` 記法を使用する
- 展開ロジックは**単純な文字列置換**（`String.prototype.replace()`）で実装する。テンプレートエンジンは導入しない
- 各 `prompts.ts` がMarkdownファイルを読み込み、MCP Promptsの `arguments` で受け取った値を変数に展開してからクライアントに返す

```typescript
// 展開ロジックの例（src/hearing/prompts.ts 内）
function renderTemplate(template: string, variables: Record<string, string>): string {
  return Object.entries(variables).reduce(
    (result, [key, value]) => result.replaceAll(`{{${key}}}`, value),
    template
  );
}
```

### 4.4 配置ルール

- プロンプトテンプレートはMarkdown形式
- コード修正なしでプロンプト内容を変更可能にするため、ソースコード（`src/`）とは分離して配置
- パッケージに同梱される

---

## 5. テストコード（`tests/`）

### 5.1 ディレクトリ構成

```
tests/
├── hearing/
│   ├── tools.test.ts           ... hearing Tools のユニットテスト
│   └── resources.test.ts       ... hearing Resources のユニットテスト
├── generate/
│   ├── tools.test.ts           ... generate Tools のユニットテスト
│   └── resources.test.ts       ... generate Resources のユニットテスト
├── core/
│   ├── storage.test.ts         ... ファイルI/Oのユニットテスト
│   ├── schema.test.ts          ... Zodスキーマのユニットテスト
│   └── config.test.ts          ... 設定読み込みのユニットテスト
└── fixtures/
    ├── sessions/               ... テスト用セッションデータ
    │   └── test-session/
    │       ├── session.json
    │       ├── hearing-result.json
    │       └── architecture.json
    ├── config/                 ... テスト用設定ファイル
    │   ├── hearing-questions.yaml
    │   └── invalid.yaml        ... 不正YAML（異常系テスト用）
    └── invalid/                ... 異常系テスト用データ
        ├── traversal-paths.json    ... パストラバーサルテスト用の不正パス一覧
        └── malformed-session.json  ... スキーマ不正のセッションデータ
```

### 5.2 配置ルール

| ルール | 説明 |
|-------|------|
| ミラー構造 | `tests/` のディレクトリ構造は `src/` と同じ階層構造にする |
| ファイル命名 | `{対象ファイル名}.test.ts` |
| フィクスチャ | テスト用の固定データは `tests/fixtures/` に配置。正常系・異常系の両方を含む |
| モック | テスト対象の外部依存（ファイルI/O等）は Vitest の `vi.mock()` でモック化 |

---

## 6. ドキュメント（`docs/`）

### 6.1 ディレクトリ構成

```
docs/
├── product-requirements.md     ... プロダクト要求定義書
├── functional-design.md        ... 機能設計書
├── architecture.md             ... 技術仕様書
├── repository-structure.md     ... リポジトリ構造定義書（本ドキュメント）
├── development-guidelines.md   ... 開発ガイドライン
└── glossary.md                 ... ユビキタス言語定義
```

### 6.2 配置ルール

- アプリケーション全体の設計・仕様を記述する永続的ドキュメント
- npm パッケージには含まない
- 図表はドキュメント内にMermaid記法で直接記述する（画像ファイルは最小限）
- 画像ファイルが必要な場合は `docs/images/` に配置（PNG / SVG推奨）

---

## 7. ステアリングファイル（`.steering/`）

### 7.1 ディレクトリ構成

```
.steering/
└── {YYYYMMDD}-{開発タイトル}/
    ├── requirements.md         ... 要求内容
    ├── design.md               ... 設計
    └── tasklist.md             ... タスクリスト
```

### 7.2 配置ルール

- 作業ごとに新しいディレクトリを作成する
- ディレクトリ名は `{YYYYMMDD}-{開発タイトル}` 形式（例: `20260213-initial-implementation`）
- npm パッケージには含まない
- 作業完了後も履歴として保持する

---

## 8. ランタイムデータディレクトリ（`~/.galley/`）

### 8.1 ディレクトリ構成

リポジトリ外に作成されるユーザーデータディレクトリ。MCPサーバー初回起動時に自動作成される。

```
~/.galley/                          ... デフォルトデータディレクトリ（--data-dir で変更可能）
├── config/                         ... ユーザーカスタム設定（任意）
│   ├── hearing-questions.yaml      ... カスタム質問テンプレート
│   ├── hearing-flow.yaml           ... カスタムフロー定義
│   ├── oci-services.yaml           ... カスタムOCIサービスカタログ
│   ├── oci-architectures.yaml      ... カスタムリファレンスアーキテクチャ
│   └── oci-terraform.yaml          ... カスタムTerraformリソース定義
├── sessions/                       ... セッションデータ
│   └── {session_id}/
│       ├── session.json            ... セッションメタデータ
│       ├── hearing-result.json     ... ヒアリング結果
│       └── architecture.json       ... アーキテクチャ設計結果
└── output/                         ... 生成物の出力先
    └── {session_id}/
        ├── summary.md              ... 要件サマリー
        ├── architecture.mmd        ... 構成図（Mermaid）
        └── terraform/
            ├── main.tf             ... メインテンプレート
            ├── variables.tf        ... 変数定義
            └── outputs.tf          ... アウトプット定義
```

### 8.2 ディレクトリの初期化

| タイミング | 動作 |
|-----------|------|
| MCPサーバー初回起動時 | `~/.galley/`、`sessions/`、`output/` を自動作成（パーミッション700） |
| `config/` | ユーザーが手動で作成（デフォルト設定をカスタマイズする場合のみ） |

### 8.3 ファイル操作ルール

| ルール | 説明 |
|-------|------|
| 書き込み | アトミック操作（一時ファイルに書き込み → rename）で行う |
| パス検証 | 書き込み前に `path.resolve()` でパストラバーサルを検証 |
| データ形式 | JSON（session.json、hearing-result.json、architecture.json） |
| 出力形式 | Markdown（summary.md）、Mermaid（.mmd）、HCL（.tf） |
| バージョニング | JSONファイルに `metadata.version` フィールドを含む |
| バックアップ | スキーママイグレーション時に `.bak` ファイルを保持 |

---

## 9. ビルド成果物（`dist/`）

### 9.1 構成

```
dist/
└── index.js                    ... エントリポイント（バンドル済み）
```

### 9.2 ルール

- `tsup` によるビルド出力。フォーマットは ESM（`"type": "module"` に対応）
- `.gitignore` に含める（Gitで追跡しない）
- ソースマップ（`.js.map`）はnpmパッケージには含めない（開発時のみローカル生成）
- npm パッケージには `dist/`、`config/`、`prompts/` を含める

---

## 10. ルートの設定ファイル

### 10.1 各ファイルの役割

| ファイル | 用途 |
|---------|------|
| `package.json` | npm パッケージ定義（詳細は 10.2 参照） |
| `tsconfig.json` | TypeScript設定。strict mode有効、`"module": "Node16"` |
| `tsup.config.ts` | tsupビルド設定。エントリポイント・出力形式（ESM）・外部依存の指定 |
| `vitest.config.ts` | Vitestテスト設定。テストファイルパターン・カバレッジ設定 |
| `eslint.config.js` | ESLintルール設定（フラットコンフィグ形式） |
| `.prettierrc` | Prettierフォーマット設定 |
| `.gitignore` | Git除外パターン（`dist/`、`node_modules/`、`.galley/` 等） |
| `CLAUDE.md` | Claude Code向けプロジェクトメモリ |
| `README.md` | プロジェクト概要・インストール手順・使用方法 |
| `LICENSE` | ライセンス |

### 10.2 `package.json` の主要フィールド

```json
{
  "name": "galley-mcp",
  "version": "0.1.0",
  "type": "module",
  "bin": {
    "galley-mcp": "dist/index.js"
  },
  "files": [
    "dist/",
    "config/",
    "prompts/",
    "README.md",
    "LICENSE"
  ]
}
```

> **`bin` フィールド**: `npx galley-mcp` で実行される際のエントリポイントを指定する。`dist/index.js` の先頭には `#!/usr/bin/env node` を含める（tsupの `banner` オプションで挿入）。

### 10.3 `.devcontainer/` の構成

開発環境の再現性を確保するためのDev Container定義。

```
.devcontainer/
├── devcontainer.json          ... Dev Container設定
└── Dockerfile                 ... カスタムDockerfile（必要な場合のみ）
```

- ベースイメージ: Node.js 22（LTS）
- Claude Code CLI をコンテナ内にインストール（`claude` コマンドが使用可能）
- ホスト側の `ANTHROPIC_API_KEY` 環境変数をコンテナに引き継ぐ
- `postCreateCommand` で `npm install` を自動実行
- 推奨VS Code拡張機能をプリインストール

### 10.4 `.vscode/` の共有方針

VS Codeを推奨エディタとして、以下のファイルをリポジトリに含める。

```
.vscode/
├── extensions.json             ... 推奨拡張機能
└── settings.json               ... エディタ設定（フォーマッタ連携等）
```

- `extensions.json`: ESLint、Prettier、Mermaid Preview 等の推奨拡張機能を記載
- `settings.json`: Prettier連携（保存時フォーマット）等、プロジェクト共通の設定のみ
- 個人設定は含めない

### 10.5 `.gitignore` の内容

```gitignore
# ビルド成果物
dist/

# 依存パッケージ
node_modules/

# ランタイムデータ（ローカルテスト用）
.galley/

# IDE（個人設定）
.vscode/*.code-workspace
.idea/

# OS
.DS_Store
Thumbs.db

# 環境変数（将来の拡張用）
.env
.env.local
```

---

## 11. npm パッケージの公開範囲

### 11.1 含む / 含まないの一覧

| 対象 | npm パッケージ | 理由 |
|------|--------------|------|
| `dist/` | 含む | ビルド済みのJavaScriptコード（ソースマップは除外） |
| `config/` | 含む | デフォルト設定ファイル（ランタイムで参照） |
| `prompts/` | 含む | プロンプトテンプレート（ランタイムで参照） |
| `README.md` | 含む | npm ページでの表示 |
| `LICENSE` | 含む | ライセンス表記 |
| `src/` | 含まない | TypeScriptソース（ビルド後は不要） |
| `tests/` | 含まない | テストコード |
| `docs/` | 含まない | 設計ドキュメント |
| `.steering/` | 含まない | 作業ドキュメント |
| `.devcontainer/` | 含まない | 開発コンテナ定義 |
| `.vscode/` | 含まない | エディタ設定 |
| `node_modules/` | 含まない | npm が自動除外 |

---

## 12. ファイル命名規則

### 12.1 ソースコード

| 対象 | 規則 | 例 |
|------|------|-----|
| TypeScriptファイル | kebab-case | `hearing-result.ts`、`storage.ts` |
| テストファイル | `{対象ファイル名}.test.ts` | `tools.test.ts`、`storage.test.ts` |
| ディレクトリ | kebab-case | `hearing/`、`generate/`、`core/` |

### 12.2 設定ファイル・プロンプト

| 対象 | 規則 | 例 |
|------|------|-----|
| YAML設定ファイル | kebab-case | `hearing-questions.yaml`、`oci-services.yaml` |
| プロンプトテンプレート | kebab-case | `start-hearing.md`、`generate-architecture.md` |

### 12.3 ランタイムデータ

| 対象 | 規則 | 例 |
|------|------|-----|
| セッションディレクトリ | UUID v4 | `a1b2c3d4-e5f6-...` |
| JSONファイル | kebab-case | `session.json`、`hearing-result.json` |
| 出力ファイル | kebab-case / Terraformの慣例 | `summary.md`、`main.tf` |
