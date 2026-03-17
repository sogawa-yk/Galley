# Requirements Document

## Intent Analysis

- **User Request**: プリセールスエンジニアのデモ環境・検証環境を、自然言語の指示だけでインフラ構築からアプリケーション生成・デプロイ・動作確認まで完全自動で構築するClaude Code Skills/Workflowsシステム
- **Request Type**: New Project（新規プロジェクト）
- **Scope Estimate**: Cross-system（Claude Code Skills/Workflows × OCI × Terraform × OCI CLI × アプリコード生成）
- **Complexity Estimate**: Complex（自然言語→ヒアリング→コード生成→インフラ構築→デプロイ→E2Eテスト）

---

## Business Context

### 対象ユーザー
- **プリセールスエンジニア**: 顧客向けデモ環境や技術検証環境を迅速に構築したい

### ユースケース
プリセールスエンジニアがClaude Codeから自然言語で「○○のデモ環境を作って」と指示すると、システムが以下を自律的に実行する：
1. ユーザーの要望からヒアリング質問リストを自動生成
2. ユーザーが質問に回答
3. 回答に基づきTerraformファイルを自動生成
4. OCI Resource Manager Stackを作成し、terraform applyを実行開始
5. **並行して** アプリケーションコードを自動生成（Claude Codeが生成）
6. **並行して** 生成したアプリコードの単体テスト・結合テストを実行
7. インフラ構築完了後、アプリケーションを自動デプロイ
8. E2Eテストを含む動作確認を自動実行
9. 結果をユーザーに報告
10. ※環境削除はユーザーがOCI ConsoleからResource Manager Stackを削除するだけで完了

---

## Functional Requirements

### FR-1: Skills/Workflows型アーキテクチャ
- Claude Codeのスキル（Skills）およびワークフロー（Workflows）として構築する
- OCI上のインスタンスプリンシパル認証済みインスタンスに対してOCI CLIコマンドを実行する
- Claude Desktop、ChatGPT等からも利用可能な設計とする（Claude Code最優先）

### FR-2: インタラクティブヒアリング
- ユーザーの自然言語による要望を受け取る
- 要望の内容に基づき、環境構築に必要な質問リストを自動生成する
- 質問は選択式（AI-DLC形式）で提供し、ユーザーの回答負荷を軽減する
- 回答内容の矛盾検出・追加質問の自動生成を行う

### FR-3: Terraformコード自動生成
- ヒアリング結果に基づき、OCIリソースのTerraformコードを自動生成する
- 対応リソース: コンピュート、ネットワーク（VCN、サブネット）、ストレージ、データベース、コンテナ（OKE、Container Instances）、OCI Functions、ロードバランサー等
- Terraformのベストプラクティスに従ったモジュール構成

### FR-4: アプリケーションコード自動生成
- ヒアリング結果に基づき、デモ用・検証用のアプリケーションコードをClaude Codeが自動生成する
- 事前に用意されたアプリケーションではなく、要件に応じた新規コードを都度生成する
- 対応アプリケーション種別:
  - Webアプリケーション（コンテナベース / OKE / Container Instances）
  - サーバーレスアプリケーション（OCI Functions）
  - Kubernetes上のマイクロサービス（OKE）

### FR-5: インフラ自動構築（OCI Resource Manager）
- 生成したTerraformコードをOCI Resource Manager Stackとして登録する
- Resource Manager経由でplan → applyを実行する
- **環境削除の簡素化**: ユーザーはOCI ConsoleからStack削除（Destroy）するだけで環境全体をクリーンアップできる
- apply結果の解析とエラーハンドリング
- OCI CLIの `oci resource-manager` コマンドを使用してStack操作を自動化

### FR-6: アプリケーション自動デプロイ
- 生成したアプリケーションコードをビルドし、OCI上にデプロイする
- コンテナイメージのビルド・プッシュ（OCIR）
- OKE/Container Instances/OCI Functionsへの自動デプロイ

### FR-7: E2Eテスト・動作確認
- デプロイ完了後、自動でE2Eテストを実行する
- アプリケーションのエンドポイントへのヘルスチェック
- 主要機能の動作確認テスト
- テスト結果のレポート生成とユーザーへの報告

### FR-8: OCI CLI操作
- インスタンスプリンシパル認証を活用したOCI CLIコマンドの実行
- リソースの作成・変更・削除・参照操作
- ステータス確認・監視

### FR-9: 並行実行による時間最適化
- Resource Manager applyは時間がかかるため、apply実行中に以下を並行して実施する:
  - アプリケーションコードの自動生成
  - 単体テスト（Unit Test）の実行
  - 結合テスト（Integration Test）の実行
- インフラ構築完了を待ってからデプロイ→E2Eテストを実行する

### FR-10: 完全自律実行
- ヒアリング回答後はユーザー介入なしで一気通貫実行する
- エラー時には自動でリカバリーを試行
- リカバリー不能な場合のみユーザーに報告
- 各ステップの進捗をリアルタイムで報告

### FR-11: 環境ライフサイクル管理
- OCI Resource Manager Stackによる環境の一括管理
- ユーザーはOCI ConsoleからStack削除（Destroy）するだけで環境全体を削除可能
- 環境削除の容易さがResource Manager採用の主要な理由

---

## Non-Functional Requirements

### NFR-1: 開発言語・技術スタック
- **開発言語**: Python
- **IaCツール**: Terraform（OCI Resource Manager経由で実行）
- **CLIツール**: OCI CLI
- **インフラ**: Oracle Cloud Infrastructure (OCI)
- **認証**: インスタンスプリンシパル（ツール側での認証不要）

### NFR-2: 対応クライアント
- **最優先**: Claude Code（CLI） — Skills/Workflows として実装
- **対応予定**: Claude Desktop（MCP経由）、ChatGPT
- クライアント非依存のコアロジックを設計し、各クライアント用のアダプターを提供

### NFR-5: 実装方針（Python + Skill/Workflow分離）
- **定型処理はPythonモジュールとして事前実装する**
  - OCI CLI呼び出しラッパー
  - OCI Resource Manager操作（Stack作成、apply、destroy、ステータス監視）
  - Terraformテンプレート生成
  - コンテナイメージビルド・プッシュ
  - E2Eテスト実行エンジン
  - 進捗レポート生成
- **Skill/WorkflowはPythonモジュールを呼び出すオーケストレーション層として設計する**
  - Skillの責務: Claude Codeに「何をすべきか」を指示し、Pythonコードの実行を指示する
  - Pythonの責務: 実際のOCI操作・ファイル生成・テスト実行などの定型処理を実行する
- **Claude Codeの自然言語能力が必要な処理はSkill/Workflow内で直接行う**
  - ヒアリング質問の動的生成
  - アプリケーションコードの生成（要件に応じた創造的なコード生成）
  - エラー分析と自律的なリカバリー判断

### NFR-3: 運用要件
- **用途**: 社内ツール / プリセールス支援
- **セキュリティ**: インスタンスプリンシパル認証に依存（ツール独自の認証なし）
- **Security Extension**: 無効（社内ツールのため）

### NFR-4: 実行環境
- OCI上のインスタンスプリンシパル認証済みComputeインスタンス上で動作
- OCI CLIがインストール済みの環境を前提とする
- Terraformがインストール済みの環境を前提とする

---

## System Context

```
+-------------------------------------------------------------+
|  User (Pre-Sales Engineer)                                   |
|  "Eコマースのデモ環境を作って"                               |
+-------------------------------------------------------------+
            |
            v
+-------------------------------------------------------------+
|  Claude Code (Skills/Workflows)                              |
|                                                              |
|  1. Hearing     - 質問リスト生成・回答収集                   |
|  2. Generate    - Terraform + App Code 自動生成              |
|  3. Deploy      - terraform apply + App Deploy               |
|  4. Verify      - E2E Test + 動作確認                        |
+-------------------------------------------------------------+
            |
            v  (OCI CLI / Terraform)
+-------------------------------------------------------------+
|  OCI Instance (Instance Principal)                           |
|  - oci resource-manager (Stack create/apply/destroy)         |
|  - docker build/push (OCIR)                                  |
|  - oci cli commands                                          |
+-------------------------------------------------------------+
            |
            v
+-------------------------------------------------------------+
|  OCI Resources                                               |
|  - VCN, Subnet, Security List                                |
|  - Compute, OKE, Container Instances                         |
|  - OCI Functions                                             |
|  - Load Balancer                                             |
|  - OCIR (Container Registry)                                 |
|  - Database (ATP, MySQL)                                     |
+-------------------------------------------------------------+
```

---

## Workflow Summary

```
User Request (自然言語)
      |
      v
[Hearing Phase]  <-- Skills/Workflows
      | 質問リスト自動生成
      | ユーザー回答
      v
[Terraform Generation]  <-- Claude Code
      | Terraform code 生成
      v
+-------------------------------------------+
|  並行実行 (Parallel Execution)            |
|                                           |
|  [Infrastructure]    [App Generation]     |
|  Resource Manager    App code 生成        |
|  Stack作成+Apply     Unit Test 実行       |
|  (時間がかかる)      Integration Test     |
+-------------------------------------------+
      |                      |
      v                      v
      +----------+-----------+
                 |
                 v  (両方完了後)
[Deploy Phase]  <-- OCI Instance
      | Container build/push
      | App deploy (OKE/CI/Functions)
      v
[Verification Phase]  <-- E2E Test
      | Health check
      | Functional test
      | Report generation
      v
[Complete] --> User に結果報告

※環境削除: OCI Console > Resource Manager > Stack削除(Destroy)
```

---

## Constraints

- OCI専用（他クラウドプロバイダーは対象外）
- インスタンスプリンシパル認証前提（API Key認証等は不要）
- Python単一言語で実装
- Claude Code Skills/Workflows形式での提供が最優先
- アプリケーションは事前に用意しない（都度Claude Codeが生成する）

---

## Development Constraints: メタ開発の課題

Claude Codeを使って、Claude Code自身のSkills/Workflowsを開発するという構造上、以下のメタ的な制約・課題が存在する。これらは後続のWorkflow Planning / Application Designで開発方法論として具体化する。

### DC-1: ファイル読み込みの競合
- 開発中のSkill/Workflowファイル（`.claude/` 配下）をClaude Codeが自動的に読み込む可能性がある
- 開発中の未完成Skillが現在のClaude Codeセッションの動作に影響を与えるリスク
- **対策方針**: 開発用ワークスペースと実行用ワークスペースの分離、またはファイル配置の工夫が必要

### DC-2: テスト環境の特殊性
- 開発したSkill/Workflowのテストには、Claude Code自体を起動して実行する必要がある
- 単体テスト（Pythonコードのロジック部分）は通常のテストフレームワークで可能
- 統合テスト（Skill/Workflowとしての動作）はClaude Code上での手動またはスクリプト実行が必要

### DC-3: Skill/Workflowのファイル構成の理解
- Claude Code Skills/Workflowsの仕様（ファイル配置、フォーマット、起動条件）を正確に理解した上で設計する必要がある
- Skill: `.claude/skills/` 配下のMarkdownファイル
- Workflow: `.claude/workflows/` 配下のMarkdownファイル（未確定 — 要調査）

### DC-4: 自己参照の回避
- 開発中のSkill/Workflowが、開発プロセス自体（AI-DLCワークフローなど）と干渉しないようにする必要がある
- CLAUDE.mdとの共存・優先順位の管理

### DC-5: エージェント分離による品質保証（CRITICAL）
- Skill/Workflowの「開発者」「実行テスター」「評価者」が同一LLMインスタンスになると、自己評価バイアスやコンテキスト汚染が発生する
- **対策方針**: Claude Codeのチーム/エージェント機能を活用し、以下の3つの役割をコンテキスト分離して開発する
  1. **開発エージェント**: Skill/Workflowのコードを作成する
  2. **テストエージェント**: 作成されたSkill/Workflowを別コンテキストで実際に実行し、結果を観測する
  3. **評価エージェント**: テスト結果を客観的に評価し、開発エージェントにフィードバックする
- 各エージェントは独立したコンテキスト（ワークツリー等）で動作させ、開発時の知識がテスト・評価を汚染しないようにする
