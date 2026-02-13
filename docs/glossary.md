# ユビキタス言語定義（Glossary）

本ドキュメントは、Galleyプロジェクトで使用する用語を統一的に定義する。ドキュメント、コード、会話のすべてにおいて、ここで定義された用語と意味を一貫して使用する。

---

## 1. プロダクト

| 日本語 | 英語 | 定義 |
|-------|------|------|
| Galley（ゲラ） | Galley | 本プロダクトの名称。OCIプリセールスエンジニア向けのAI支援MCPサーバー。印刷用語で「校正刷り」を意味し、本番前の試作版を素早く作り上げるプロセスがプリセールスのデモ作成と重なることに由来する |

---

## 2. ドメイン用語

### 2.1 ビジネスドメイン

| 日本語 | 英語 | 定義 | コード上の命名 |
|-------|------|------|--------------|
| プリセールスエンジニア | Presales Engineer | 自社クラウドベンダーに所属する技術営業。顧客向けにアーキテクチャ提案やデモ環境構築を行う。Galleyのターゲットユーザー | — |
| 案件 | Project | 顧客向けの提案・デモ準備の一単位。1案件につき1セッションを作成する | `project_description` |
| デモ | Demo | 顧客に提示するクラウドアーキテクチャの設計成果物。MVP段階ではドキュメント（構成図・IaCテンプレート）を指す。実環境のデプロイは含まない | — |
| 業種 | Industry | 顧客の業種分類（製造業、金融、小売等） | `industry` |
| 案件種別 | Project Type | 案件の技術的分類（新規構築、マイグレーション、モダナイゼーション等） | `project_type` |
| ナレッジストア | Knowledge Store | 社内の過去案件データやナレッジを蓄積・検索するための共有データベース。Phase 2以降で導入予定。MVP段階では未対応 | — |

### 2.2 ヒアリングドメイン

| 日本語 | 英語 | 定義 | コード上の命名 |
|-------|------|------|--------------|
| ヒアリング | Hearing | AIクライアントを通じて行う選択式の要件聞き取りプロセス。8〜12問で構成される | `hearing` |
| セッション | Session | 1案件に対する1回のヒアリング〜生成の作業単位。UUID で識別される | `Session`、`session_id` |
| 質問テンプレート | Hearing Questions | ヒアリングで使用する質問カテゴリと選択肢の定義。YAMLファイルで管理される | `hearing-questions.yaml` |
| フロー定義 | Hearing Flow | ヒアリングの進行順序と分岐条件の定義 | `hearing-flow.yaml` |
| 質問カテゴリ | Question Category | ヒアリングの質問を分類するグループ。案件概要、規模、トラフィック等の10カテゴリで構成（下記 2.3 参照） | `category` |
| 回答 | Answer | ヒアリングの各質問に対するユーザーの応答。選択、自由入力、推測、未回答のいずれか | `save_answer`、`AnsweredItem` |
| ヒアリング結果 | Hearing Result | ヒアリングで収集した全回答の構造化データ。アーキテクチャ生成の入力となる | `HearingResult` |
| 案件概要 | Project Description | ユーザーが最初に入力する案件の自然言語テキスト。ヒアリングの出発点 | `project_description` |

### 2.3 質問カテゴリとデータフィールドの対応

| # | カテゴリ（日本語） | カテゴリ（英語） | requirementsフィールド | 含まれるフィールド |
|---|-----------------|----------------|---------------------|------------------|
| Q1 | 案件概要 | Project Overview | `project_overview` | `description`、`industry`、`project_type` |
| Q2 | 規模 | Scale | `requirements.scale` | `concurrent_users`、`total_users` |
| Q3 | トラフィック特性 | Traffic | `requirements.traffic` | `spike_pattern`、`peak_tps` |
| Q4 | データベース | Database | `requirements.database` | `existing_db`、`migration_required`、`data_volume` |
| Q5 | ネットワーク | Network | `requirements.network` | `multi_region`、`on_premises_connection` |
| Q6 | セキュリティ・認証 | Security | `requirements.security` | `auth_method`、`compliance` |
| Q7 | 可用性・DR | Availability | `requirements.availability` | `sla_target`、`dr_requirement`、`backup_policy` |
| Q8 | パフォーマンス | Performance | `requirements.performance` | `latency_requirement`、`throughput_requirement` |
| Q9 | 運用・監視 | Operations | `requirements.operations` | `monitoring`、`log_retention` |
| Q10 | 予算・スケジュール | Budget & Schedule | `requirements.budget_schedule` | `cost_constraint`、`demo_deadline` |

### 2.4 推測ドメイン

| 日本語 | 英語 | 定義 | コード上の命名 |
|-------|------|------|--------------|
| 推測 | Estimation | ユーザーが「わからない」と回答した項目に対し、AIが生成する仮の値と根拠 | `Estimation`、`estimation` |
| 推測値 | Estimated Value | AIが提示する仮の回答値 | `value`（`source: "estimated"` の場合） |
| 推測根拠 | Reasoning | 推測値の理由説明 | `reasoning` |
| 参照元情報 | Source Info | 推測根拠の出典（URL、公開事例の説明等） | `source_info` |
| 信頼度ラベル | Confidence Label | 推測根拠の出典分類。下記3種類 | `ConfidenceLabel`、`confidence_label` |
| 公開事例 | Public Reference | 公開情報（リファレンスアーキテクチャ、事例記事等）に基づく推測 | `"public_reference"` |
| 一般推計 | General Estimate | 業界の一般的なベストプラクティスに基づく推測 | `"general_estimate"` |
| 社内実績 | Internal Record | 社内の過去案件データに基づく推測（MVP段階では未対応） | `"internal_record"` |

### 2.5 生成ドメイン

| 日本語 | 英語 | 定義 | コード上の命名 |
|-------|------|------|--------------|
| アーキテクチャ | Architecture | ヒアリング結果に基づいて設計されたクラウドインフラ構成 | `ArchitectureOutput` |
| コンポーネント | Component | アーキテクチャを構成する個々のクラウドサービス要素 | `Component`、`components` |
| 選定理由 | Component Decision | 各コンポーネントを採用した技術的根拠 | `ComponentDecision`、`decisions` |
| 警告 | Warning | アーキテクチャ設計で検出されたアンチパターンや未確認リスク | `Warning`、`warnings` |
| アンチパターン | Anti-pattern | 避けるべき設計パターン（単一障害点、セキュリティグループの全開放等） | — |
| 要件サマリー | Requirements Summary | 確定事項（✅）、推測（🔶）、未確認（⚠️）の3区分で整理した要件一覧 | `export_summary` |
| 構成図 | Architecture Diagram | Mermaid記法で記述されたクラウド構成の図 | `export_mermaid`、`.mmd` |
| IaCテンプレート | IaC Template | Terraform（OCI Provider）形式のインフラ定義コード | `export_iac`、`.tf` |

### 2.6 回答の出所（Source）

| 日本語 | 英語 | 定義 | コード上の値 |
|-------|------|------|------------|
| ユーザー選択 | User Selected | ユーザーが番号選択肢から回答した | `"user_selected"` |
| ユーザー自由入力 | User Free Text | ユーザーが自由テキストで回答した | `"user_free_text"` |
| 推測 | Estimated | AIが推測し、ユーザーが承認した | `"estimated"` |
| 未回答 | Not Answered | 回答されなかった項目 | `"not_answered"` |

### 2.7 セッションステータス

| 日本語 | 英語 | 定義 | コード上の値 |
|-------|------|------|------------|
| 進行中 | In Progress | ヒアリングまたは生成が進行中。回答の追加・変更が可能 | `"in_progress"` |
| 完了 | Completed | ヒアリングが完了し、結果が確定している。回答の追加は不可 | `"completed"` |

---

## 3. MCPプロトコル用語

### 3.1 基本概念

| 用語 | 定義 | Galleyでの使い方 |
|------|------|----------------|
| MCP (Model Context Protocol) | AIクライアントとサーバー間の通信プロトコル。Anthropicが策定 | GalleyはMCPサーバーとして実装される |
| MCPサーバー | MCPプロトコルに従ってResources/Tools/Promptsを提供するプロセス | `galley-mcp` パッケージ |
| AIクライアント | MCPサーバーに接続してLLMの機能を提供するアプリケーション | Claude Desktop、ChatGPT等。ユーザーが選択 |
| Resources | AIクライアントにコンテキストを提供する読み取り専用データ | 質問テンプレート、OCIサービスカタログ、セッションデータ |
| Tools | AIクライアントが呼び出すアクション（副作用を伴う操作） | セッション作成、回答保存、ファイル出力等 |
| Prompts | 再利用可能なプロンプトテンプレート。AIクライアントに対するLLMの振る舞い指示 | ヒアリング開始、アーキテクチャ生成 |
| stdioトランスポート | 標準入出力（stdin/stdout）を通じたJSON-RPC通信 | GalleyのMCPサーバーが使用する通信方式 |
| ケーパビリティ | Capabilities | MCPサーバーが初期化時にクライアントに宣言する機能一覧（Resources、Tools、Prompts、Logging等） |
| listChanged | Resourceリストの変更をクライアントに通知する機能 | セッション作成・削除時に通知 |

### 3.2 Galleyが提供するTools

| Tool名 | 所属モジュール | 概要 |
|--------|-------------|------|
| `create_session` | hearing | 新規セッションを作成 |
| `save_answer` | hearing | 回答を1件保存 |
| `save_answers_batch` | hearing | 回答を一括保存（Tool呼び出し回数の削減用） |
| `complete_hearing` | hearing | ヒアリングを完了にする |
| `get_hearing_result` | hearing | ヒアリング結果を取得 |
| `list_sessions` | hearing | セッション一覧を取得 |
| `delete_session` | hearing | セッションを削除 |
| `save_architecture` | generate | アーキテクチャ設計を保存 |
| `export_summary` | generate | 要件サマリーをMarkdownファイルに出力 |
| `export_mermaid` | generate | 構成図をMermaidファイルに出力 |
| `export_iac` | generate | IaCテンプレートをファイルに出力 |
| `export_all` | generate | 全成果物を一括出力 |

### 3.3 Galleyが提供するPrompts

| Prompt名 | 所属モジュール | 概要 |
|----------|-------------|------|
| `start-hearing` | hearing | ヒアリングを開始するプロンプト |
| `resume-hearing` | hearing | 中断したヒアリングを再開するプロンプト |
| `generate-architecture` | generate | ヒアリング結果からアーキテクチャを生成するプロンプト |

### 3.4 Galleyが提供するResources

| Resource URI | 所属モジュール | 概要 |
|-------------|-------------|------|
| `galley://templates/hearing-questions` | hearing | 質問カテゴリテンプレート |
| `galley://templates/hearing-flow` | hearing | ヒアリングフロー進行ルール |
| `galley://schemas/hearing-result` | hearing | ヒアリング結果JSONスキーマ |
| `galley://sessions` | hearing | 保存済みセッション一覧 |
| `galley://sessions/{session_id}` | hearing | 特定セッションの詳細データ |
| `galley://references/oci-services` | generate | OCIサービスカタログ |
| `galley://references/oci-architectures` | generate | OCIリファレンスアーキテクチャ集 |
| `galley://references/oci-terraform` | generate | OCI Terraform Providerリソース一覧 |

---

## 4. 技術用語

### 4.1 OCI（Oracle Cloud Infrastructure）

| 用語 | 定義 | Galleyでの使い方 |
|------|------|----------------|
| OCI | Oracle社が提供するクラウドプラットフォーム | Galleyが対象とするクラウド基盤 |
| OCIサービスカタログ | OCI主要20サービスの名称・用途・制約をまとめたリファレンス | `config/oci-services.yaml` として提供 |
| リファレンスアーキテクチャ | 業種・ユースケース別の推奨構成パターン | `config/oci-architectures.yaml` として提供 |
| OCI Terraform Provider | TerraformでOCIリソースを管理するためのプラグイン | IaCテンプレート生成時にリソース名を参照。`config/oci-terraform.yaml` |

### 4.2 外部ツール・フォーマット

| 用語 | 定義 | Galleyでの使い方 |
|------|------|----------------|
| Terraform | HashiCorp社のIaCツール。HCL（HashiCorp Configuration Language）で記述 | アーキテクチャ生成結果のIaCテンプレート出力形式 |
| Mermaid | テキストベースのダイアグラム記法。Markdownに埋め込み可能 | アーキテクチャ構成図の出力形式（`.mmd` ファイル） |
| Zod | TypeScript向けのスキーマ宣言・バリデーションライブラリ | Tool引数、JSON/YAML設定ファイルのランタイムバリデーション |
| MCP Inspector | MCP公式のデバッグツール。ブラウザUIでResources/Tools/Promptsを操作できる | 統合テストに使用 |

### 4.3 内部アーキテクチャ

| 用語 | 定義 | 備考 |
|------|------|------|
| hearingモジュール | ヒアリングフローの状態管理とデータ永続化を担当する内部モジュール | functional-design.md では「galley-hearing サーバー」と表記。実装は単一MCPサーバー内の内部モジュール |
| generateモジュール | アーキテクチャ設計結果の保存とファイル出力を担当する内部モジュール | functional-design.md では「galley-generate サーバー」と表記。実装は単一MCPサーバー内の内部モジュール |
| coreモジュール | ファイルI/O、設定読み込み、バリデーション、ログ出力等の共通基盤 | hearingとgenerateの両方が依存する最下層モジュール |
| アトミック書き込み | 一時ファイルへの書き込み→renameによる安全なファイル更新手法 | プロセス中断時のデータ破損を防止。`core/storage.ts` で実装 |
| データディレクトリ | Galleyのランタイムデータを保存するディレクトリ | `~/.galley/`（`--data-dir` で変更可能） |

---

## 5. 略語一覧

| 略語 | 正式名称 | 日本語 |
|------|---------|--------|
| MCP | Model Context Protocol | モデルコンテキストプロトコル |
| OCI | Oracle Cloud Infrastructure | オラクルクラウドインフラストラクチャ |
| IaC | Infrastructure as Code | インフラストラクチャ・アズ・コード |
| MVP | Minimum Viable Product | 実用最小限の製品 |
| LLM | Large Language Model | 大規模言語モデル |
| SDK | Software Development Kit | ソフトウェア開発キット |
| ESM | ECMAScript Modules | ECMAScriptモジュール |
| JSON-RPC | JSON Remote Procedure Call | JSONリモートプロシージャコール |
| UUID | Universally Unique Identifier | 汎用一意識別子 |
| SLA | Service Level Agreement | サービスレベル合意 |
| DR | Disaster Recovery | 災害復旧 |
| TPS | Transactions Per Second | 秒間トランザクション数 |
| VCN | Virtual Cloud Network | 仮想クラウドネットワーク（OCI） |
| OKE | Oracle Container Engine for Kubernetes | OCIのKubernetesサービス |
| IAM | Identity and Access Management | アイデンティティ・アクセス管理 |
| WAF | Web Application Firewall | ウェブアプリケーションファイアウォール |
| HCL | HashiCorp Configuration Language | HashiCorp設定言語（Terraformの記述言語） |
| YAML | YAML Ain't Markup Language | 設定ファイル記述言語 |

---

## 6. コード上の型名マッピング

ドメイン概念とTypeScript型名の対応一覧。

### 6.1 ヒアリング関連（`src/types/hearing.ts`）

| ドメイン概念 | TypeScript型 | 説明 |
|------------|-------------|------|
| ヒアリング結果 | `HearingResult` | ヒアリング全体の構造化データ。`metadata` + `project_overview` + `requirements` |
| 回答項目 | `AnsweredItem` | 個々の質問に対する回答。`value` + `source` + `estimation?` |
| 推測情報 | `Estimation` | 推測の詳細。`confidence_label` + `reasoning` + `source_info` |
| 信頼度ラベル | `ConfidenceLabel` | `"public_reference" \| "general_estimate"` （将来 `"internal_record"` を追加） |
| 回答の出所 | `AnswerSource` | `"user_selected" \| "user_free_text" \| "estimated" \| "not_answered"` |

### 6.2 セッション関連（`src/types/session.ts`）

| ドメイン概念 | TypeScript型 | 説明 |
|------------|-------------|------|
| セッション | `Session` | セッションのメタデータ。`session_id` + `status` + `project_description` + タイムスタンプ |
| セッションステータス | `SessionStatus` | `"in_progress" \| "completed"` |

### 6.3 アーキテクチャ関連（`src/types/architecture.ts`）

| ドメイン概念 | TypeScript型 | 説明 |
|------------|-------------|------|
| アーキテクチャ出力 | `ArchitectureOutput` | 設計結果全体。コンポーネント + 選定理由 + 警告 |
| コンポーネント | `Component` | 個々のクラウドサービス要素 |
| コンポーネント選定理由 | `ComponentDecision` | 選定の技術的根拠 |
| 警告 | `Warning` | アンチパターン検出・未確認リスク |

### 6.4 エラー関連（`src/core/errors.ts`）

| ドメイン概念 | TypeScript型 | 説明 |
|------------|-------------|------|
| エラー | `GalleyError` | アプリケーション固有のエラークラス |
| エラーコード | `GalleyErrorCode` | `"SESSION_NOT_FOUND"` 等のエラー種別 |

---

## 7. 用語使い分けガイド

### 紛らわしい用語の整理

| 混同しやすい用語 | Galleyでの使い分け |
|----------------|------------------|
| セッション vs ヒアリング | **セッション**は作業単位全体（ヒアリング〜生成）を指す。**ヒアリング**はセッション内の質問応答フェーズを指す |
| 推測 vs 推定 | **推測**（Estimation）を統一用語とする。「推定」は使用しない |
| アーキテクチャ vs 構成図 | **アーキテクチャ**はクラウドインフラ設計全体を指す。**構成図**（Architecture Diagram）はMermaid形式の図表出力を指す |
| AIクライアント vs ユーザー | **AIクライアント**はClaude Desktop等のアプリケーションを指す。**ユーザー**はプリセールスエンジニア（人間）を指す |
| テンプレート vs プロンプト | **テンプレート**は質問定義等の設定データ（`config/`）を指す。**プロンプト**はAIクライアントへのLLM指示文（`prompts/`）を指す |
| 設定ファイル vs データファイル | **設定ファイル**はYAML形式の構成定義（`config/`、`~/.galley/config/`）。**データファイル**はJSON形式のセッション・ヒアリング結果（`~/.galley/sessions/`） |
| MCP Tool vs ツール | MCPプロトコルの**Tool**（`create_session` 等）を指す場合は英語表記。一般的な開発ツール（ESLint等）を指す場合は日本語で「ツール」 |
| galley-hearing / galley-generate vs hearing / generate モジュール | **galley-hearing / galley-generate** は機能設計書での論理的なサーバー区分を指す。実装上は単一MCPサーバー内の **hearing / generate モジュール** として実装される |
| デフォルト設定 vs ユーザー設定 | **デフォルト設定**はパッケージ同梱の `config/` ディレクトリ。**ユーザー設定**は `~/.galley/config/` にユーザーが手動配置する上書き用設定 |
