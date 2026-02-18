# プロジェクト用語集 (Glossary)

## 概要

このドキュメントは、Galleyプロジェクト内で使用される用語の定義を管理します。

**更新日**: 2026-02-17

## ドメイン用語

### Galley

**定義**: Python + FastMCPで実装するOCIプリセールス支援MCPサーバー

**説明**: 利用者はClaude Desktop等のMCPホストからGalleyに接続し、要件のヒアリングからアーキテクチャ設計、インフラ構築、アプリケーションデプロイまでを一貫して行える。

**関連用語**: [MCPサーバー](#mcpサーバー)、[MCPホスト](#mcpホスト)

**使用例**:
- 「Galleyに接続して検証環境を構築する」
- 「GalleyのMCPツールを使ってヒアリングを開始する」

**英語表記**: Galley

### セッション

**定義**: ヒアリングから設計・構築までの一連の作業を管理する単位

**説明**: `galley:create_session` で作成され、ヒアリング回答、ヒアリング結果、アーキテクチャ、Terraformファイル、アプリケーションコード等のデータを保持する。セッションIDで一意に識別される。

**関連用語**: [ヒアリング](#ヒアリング)、[アーキテクチャ](#アーキテクチャ)

**使用例**:
- 「新しいセッションを作成する」
- 「セッションIDを指定してヒアリング結果を取得する」

**英語表記**: Session

### ヒアリング

**定義**: 利用者の要件を対話的に聞き出し、構造化するプロセス

**説明**: ヒアリングフロー定義に従って質問を提示し、回答を保存する。完了時に要件を構造化した「ヒアリング結果」を生成する。

**関連用語**: [セッション](#セッション)、[ヒアリング結果](#ヒアリング結果)

**使用例**:
- 「ヒアリングを開始する」
- 「ヒアリングの回答を保存する」
- 「ヒアリングを完了して結果を取得する」

**英語表記**: Hearing

### ヒアリング結果

**定義**: ヒアリング完了後に生成される構造化された要件情報

**説明**: 要件サマリー、構造化された要件リスト（カテゴリ・優先度付き）、制約事項を含む。自動設計モードのインプットとして使用される。

**関連用語**: [ヒアリング](#ヒアリング)、[自動設計モード](#自動設計モード)

**英語表記**: Hearing Result

### アーキテクチャ

**定義**: OCIサービスのコンポーネント構成と接続関係を定義したもの

**説明**: コンポーネント（OCIサービス）の一覧、コンポーネント間の接続関係、各コンポーネントの設定を保持する。自動設計モードまたは対話型設計モードで作成される。

**関連用語**: [コンポーネント](#コンポーネント)、[接続](#接続)、[バリデーション](#バリデーション)

**使用例**:
- 「アーキテクチャにOKEコンポーネントを追加する」
- 「アーキテクチャをバリデーションする」
- 「アーキテクチャをMermaid形式でエクスポートする」

**英語表記**: Architecture

### コンポーネント

**定義**: アーキテクチャを構成するOCIサービスの単位

**説明**: サービス種別（例: oke, adb, apigateway）、表示名、サービス固有の設定を持つ。コンポーネントIDで一意に識別される。

**関連用語**: [アーキテクチャ](#アーキテクチャ)、[接続](#接続)

**使用例**:
- 「OKEコンポーネントを追加する」
- 「ADBコンポーネントの設定をPrivate Endpointに変更する」

**英語表記**: Component

### 接続

**定義**: アーキテクチャ内のコンポーネント間の通信経路

**説明**: 接続元・接続先のコンポーネントID、接続種別（private_endpoint、public、service_gateway、vcn_peering）を持つ。バリデーション時に接続要件のチェック対象となる。

**関連用語**: [コンポーネント](#コンポーネント)、[バリデーション](#バリデーション)

**英語表記**: Connection

### バリデーション

**定義**: アーキテクチャ構成がOCI固有の制約やベストプラクティスに準拠しているかを検証するプロセス

**説明**: Object Storage上のバリデーションルール（YAML）に基づいてアーキテクチャを検証し、エラー・警告・情報の3段階で結果を返す。

**関連用語**: [アーキテクチャ](#アーキテクチャ)、[バリデーションルール](#バリデーションルール)

**使用例**:
- 「アーキテクチャのバリデーションを実行する」
- 「バリデーション結果に従ってPrivate Endpointを設定する」

**英語表記**: Validation

### バリデーションルール

**定義**: アーキテクチャ検証に使用するOCI固有の制約知識をデータとして定義したもの

**説明**: サービス間の接続要件、リージョン別サービス可用性、シェイプ制約、ネットワークベストプラクティスなどをYAML形式で管理。開発者が随時追加・更新可能。

**関連用語**: [バリデーション](#バリデーション)

**英語表記**: Validation Rule

### 自動設計モード

**定義**: ヒアリング結果からGalleyが推奨アーキテクチャを自動生成するモード

**説明**: 初期案を素早く作成したいとき、詳しくない領域の参考にしたいとき向け。LLMがヒアリング結果を分析し、推奨構成を `galley:save_architecture` で保存する。

**関連用語**: [対話型設計モード](#対話型設計モード)、[ヒアリング結果](#ヒアリング結果)

**英語表記**: Automatic Design Mode

### 対話型設計モード

**定義**: 利用者がアーキテクチャを主導で組み立て、Galleyが支援するモード

**説明**: 利用者がコンポーネントの追加・削除・設定変更を行い、Galleyがフィードバックやバリデーションを提供する。既にサービス構成が決まっている場合に適する。

**関連用語**: [自動設計モード](#自動設計モード)、[バリデーション](#バリデーション)

**英語表記**: Interactive Design Mode

### テンプレート

**定義**: 検証で頻繁に使うアプリケーション構成の再利用可能な雛形

**説明**: アプリケーションコード、Kubernetesマニフェスト、Terraform定義、メタデータ（`template.json`）で構成される。Object Storage上の所定ディレクトリに配置。

**関連用語**: [テンプレートストア](#テンプレートストア)、[スキャフォールド](#スキャフォールド)

**使用例**:
- 「テンプレート一覧を確認する」
- 「REST API + ADBテンプレートからプロジェクトを生成する」

**英語表記**: Template

### テンプレートストア

**定義**: テンプレートを格納・管理するObject Storage上の領域

**説明**: `templates/` プレフィックス配下にテンプレートごとのディレクトリが配置される。開発者がObject Storageにアップロードするだけでテンプレートを追加可能。

**関連用語**: [テンプレート](#テンプレート)

**英語表記**: Template Store

### スキャフォールド

**定義**: テンプレートからパラメータに基づいてプロジェクトを生成するプロセス

**説明**: `galley:scaffold_from_template` でテンプレートをベースにプロジェクトを生成する。パラメータで DBスキーマ、APIエンドポイント、環境変数等をカスタマイズ可能。

**関連用語**: [テンプレート](#テンプレート)

**英語表記**: Scaffold

### 自動デバッグループ

**定義**: LLMがTerraformエラーを解析→コード修正→再実行を自動的に繰り返すプロセス

**説明**: GalleyのMCPツール（`run_terraform_plan`）がエラー詳細を返し、LLMがエラーを解析してTerraformコードを修正し、再度planを実行する。成功するまで繰り返される。

**関連用語**: [Terraform](#terraform)

**英語表記**: Automatic Debug Loop

## 技術用語

### FastMCP

**定義**: Python向けのMCPサーバーフレームワーク

**本プロジェクトでの用途**: Galley MCPサーバーの実装基盤。ツール、リソース、プロンプトの登録とSSE/StreamableHTTPトランスポートを提供。

**バージョン**: 最新安定版

**関連ドキュメント**: [アーキテクチャ設計書](./architecture.md)

### OCI SDK for Python

**定義**: Oracle Cloud InfrastructureのPython用公式SDK

**本プロジェクトでの用途**: Resource Principal認証、Object Storage操作、Resource Manager連携、その他OCI APIアクセス。

**バージョン**: 最新安定版

**関連ドキュメント**: [アーキテクチャ設計書](./architecture.md)

### Pydantic

**定義**: Pythonのデータバリデーション・シリアライゼーションライブラリ

**本プロジェクトでの用途**: データモデル定義（Session、Architecture等）、MCPツールパラメータのバリデーション、JSON変換。

**バージョン**: 2.x

### Terraform

**定義**: HashiCorpが提供するInfrastructure as Code（IaC）ツール

**本プロジェクトでの用途**:
1. Galleyコンテナ内でのOCIリソースプロビジョニング（検証環境構築）
2. 配布用インフラ定義（利用者がGalley環境を構築するため）

**バージョン**: 1.x

### Resource Manager

**定義**: OCIが提供するTerraformベースのマネージドIaCサービス

**本プロジェクトでの用途**: 本番デプロイや顧客引き渡し用のインフラ管理。ジョブキュー経由でplan/applyを実行。

**関連ドキュメント**: [機能設計書 F10](./functional-design.md)

### MCPサーバー

**定義**: MCPプロトコルを実装し、ツール・リソース・プロンプトを公開するサーバーアプリケーション

**本プロジェクトでの適用**: GalleyはFastMCPベースのMCPサーバーとして実装される。

### MCPホスト

**定義**: MCPサーバーに接続し、ツールを呼び出すクライアントアプリケーション

**本プロジェクトでの適用**: Claude Desktop、claude.ai等のLLMアプリケーションがMCPホストとして動作する。

### MCPツール

**定義**: MCPサーバーが公開する実行可能な操作（関数）

**本プロジェクトでの適用**: `galley:create_session`、`galley:save_answer`等のツールをFastMCPの`@mcp.tool()`で定義。

### MCPリソース

**定義**: MCPサーバーが公開する読み取り専用のデータソース

**本プロジェクトでの適用**: ヒアリング質問定義、OCIサービス一覧等をFastMCPの`@mcp.resource()`で定義。

### MCPプロンプト

**定義**: MCPサーバーが公開する再利用可能なプロンプトテンプレート

**本プロジェクトでの適用**: ヒアリング開始・設計支援・デプロイ支援プロンプトを`@mcp.prompt()`で定義。

## 略語・頭字語

### MCP

**正式名称**: Model Context Protocol

**意味**: LLMとツール・データソースを接続するためのオープンプロトコル

**本プロジェクトでの使用**: GalleyはMCPサーバーとして実装され、MCPホスト（Claude Desktop等）からツールを呼び出す。

### OCI

**正式名称**: Oracle Cloud Infrastructure

**意味**: Oracleが提供するクラウドインフラストラクチャサービス

**本プロジェクトでの使用**: Galleyが設計・構築・管理するクラウド環境のプラットフォーム。

### OKE

**正式名称**: Oracle Kubernetes Engine

**意味**: OCIのマネージドKubernetesサービス

**本プロジェクトでの使用**: アプリケーションのデプロイ先として使用。kubectlで操作。

### ADB

**正式名称**: Autonomous Database

**意味**: OCIのフルマネージドデータベースサービス

**本プロジェクトでの使用**: アーキテクチャコンポーネントとして利用。Private Endpoint接続のバリデーション対象。

### OCIR

**正式名称**: Oracle Cloud Infrastructure Registry

**意味**: OCIのコンテナイメージレジストリサービス

**本プロジェクトでの使用**: Galleyコンテナイメージの公開先、アプリケーションビルドイメージの格納先。

### IaC

**正式名称**: Infrastructure as Code

**意味**: インフラストラクチャをコードで定義・管理する手法

**本プロジェクトでの使用**: TerraformによるOCIリソースのプロビジョニング。

### SSE

**正式名称**: Server-Sent Events

**意味**: サーバーからクライアントへの一方向リアルタイム通信プロトコル

**本プロジェクトでの使用**: MCPのトランスポートプロトコルの一つ。

### VCN

**正式名称**: Virtual Cloud Network

**意味**: OCI上の仮想ネットワーク

**本プロジェクトでの使用**: Galleyインフラのネットワーク構成、検証環境のネットワーク構成。

### Container Instance

**正式名称**: OCI Container Instances

**意味**: OCIのサーバーレスコンテナ実行環境

**本プロジェクトでの使用**: Galley MCPサーバーの実行環境。Dockerコンテナを直接実行する。

### Dynamic Group

**正式名称**: Dynamic Group

**意味**: リソース属性（OCID、コンパートメント等）に基づいて動的にメンバーが決定されるOCIのグループ

**本プロジェクトでの使用**: Container InstanceをDynamic Groupに含め、Resource Principal認証を有効にする。

### API Gateway

**正式名称**: OCI API Gateway

**意味**: OCIのマネージドAPIゲートウェイサービス

**本プロジェクトでの使用**: MCPエンドポイントのHTTPS終端、URLトークン認証を担当。

## アーキテクチャ用語

### レイヤードアーキテクチャ

**定義**: システムを役割ごとに複数の層に分割し、上位層から下位層への一方向の依存関係を持たせる設計パターン

**本プロジェクトでの適用**:
```
MCPプロトコル層 (tools/, resources/, prompts/)
    ↓
サービス層 (services/)
    ↓
データアクセス層 (storage/)
    ↓
外部システム (OCI API, Object Storage)
```

**関連コンポーネント**: GalleyServer、各Service、StorageService

### Resource Principal認証

**定義**: OCIリソース（Container Instance等）に割り当てられたアイデンティティを使用してOCI APIを認証する方式

**本プロジェクトでの適用**: Container InstanceがDynamic Groupに含まれ、IAM PolicyによりOCIリソースの操作権限を取得する。APIキーの配布・管理が不要。

**関連コンポーネント**: OCIClientFactory、Dynamic Group、IAM Policy

### URLトークン認証

**定義**: URLのクエリパラメータにトークンを含めて認証する方式

**本プロジェクトでの適用**: MCPエンドポイントの認証に使用。`terraform apply` 時にランダム生成されたトークンをAPI Gatewayが検証する。

**関連コンポーネント**: API Gateway、配布用Terraform

## ステータス・状態

### セッションステータス（永続化モデル）

| ステータス | 意味 | 遷移条件 | 次の状態 |
|----------|------|---------|---------|
| `in_progress` | 進行中 | セッション作成時の初期状態 | `completed` |
| `completed` | ヒアリング完了 | `complete_hearing` の実行 | — |

### ワークフロー状態（論理状態）

機能設計書の状態遷移図に示される各状態（Created、Hearing、HearingCompleted、Designing、Validated、Building、Deployed等）は、永続化される `status` フィールドではなく、セッション内のデータ（answers、hearing_result、architecture等の有無）から論理的に導出される。詳細は [機能設計書](./functional-design.md) の「永続化ステータスとワークフロー状態の関係」を参照。

### バリデーション重要度

| 重要度 | 意味 | 対応 |
|--------|------|------|
| `error` | 構成が動作しない致命的な問題 | 修正必須 |
| `warning` | 推奨事項に反する構成 | 修正推奨 |
| `info` | 参考情報・ベストプラクティス提案 | 任意 |

## データモデル用語

### Session

**定義**: ヒアリングから設計・構築までの全データを保持するルートエンティティ

**主要フィールド**:
- `id`: UUID v4
- `status`: `"in_progress"` | `"completed"`
- `answers`: 質問ID → 回答のマッピング
- `hearing_result`: ヒアリング結果（完了後に設定）
- `architecture`: アーキテクチャ（設計後に設定）

**関連エンティティ**: Answer、HearingResult、Architecture

**永続化先**: Object Storage `sessions/{session_id}/session.json`

### Answer

**定義**: ヒアリングの個別質問に対する回答データ

**主要フィールド**:
- `question_id`: 質問ID
- `value`: 回答値（テキストまたは複数選択）
- `answered_at`: 回答日時

**関連エンティティ**: Session（Session.answers辞書内に格納）

### HearingResult

**定義**: ヒアリング完了時に生成される構造化された要件情報

**主要フィールド**:
- `summary`: 要件サマリー（Markdown）
- `requirements`: 構造化された要件リスト（カテゴリ・優先度付き）
- `constraints`: 制約事項

**関連エンティティ**: Session

### ValidationResult

**定義**: アーキテクチャバリデーションの個別検証結果

**主要フィールド**:
- `severity`: 重要度（error / warning / info）
- `rule_id`: バリデーションルールID
- `message`: 問題の説明
- `affected_components`: 影響コンポーネントID
- `recommendation`: 推奨する対応

**関連エンティティ**: Architecture

### TerraformResult

**定義**: Terraform実行（plan / apply / destroy）の結果データ

**主要フィールド**:
- `success`: 実行成功フラグ
- `command`: 実行コマンド種別
- `stdout` / `stderr`: 標準出力・エラー出力
- `exit_code`: 終了コード

### DeployResult

**定義**: アプリケーションデプロイの結果データ

**主要フィールド**:
- `success`: デプロイ成功フラグ
- `endpoint`: アクセスエンドポイント
- `rolled_back`: 自動ロールバック実行フラグ

### AppStatus

**定義**: デプロイ済みアプリケーションの現在のステータス

**主要フィールド**:
- `status`: `"not_deployed"` | `"deploying"` | `"running"` | `"failed"`
- `endpoint`: アクセスエンドポイント
- `health_check`: 直近のヘルスチェック結果

## エラー・例外

### SessionNotFoundError

**クラス名**: `SessionNotFoundError`

**発生条件**: 指定されたセッションIDに対応するセッションがObject Storageに存在しない場合

**対処方法**: 正しいセッションIDを指定してリトライ

### ValidationError

**クラス名**: `ValidationError`

**発生条件**: MCPツールのパラメータがバリデーションに失敗した場合

**対処方法**: エラー詳細に従って入力パラメータを修正

### TerraformError

**クラス名**: `TerraformError`

**発生条件**: `terraform plan` / `terraform apply` が非ゼロの終了コードを返した場合

**対処方法**: `stderr` のエラーメッセージを分析し、Terraformコードを修正して再実行（自動デバッグループ）

## 索引

### あ行
- [アーキテクチャ](#アーキテクチャ) — ドメイン用語
- [自動デバッグループ](#自動デバッグループ) — ドメイン用語
- [自動設計モード](#自動設計モード) — ドメイン用語

### か行
- [コンポーネント](#コンポーネント) — ドメイン用語

### さ行
- [スキャフォールド](#スキャフォールド) — ドメイン用語
- [セッション](#セッション) — ドメイン用語
- [接続](#接続) — ドメイン用語

### た行
- [対話型設計モード](#対話型設計モード) — ドメイン用語
- [テンプレート](#テンプレート) — ドメイン用語
- [テンプレートストア](#テンプレートストア) — ドメイン用語

### は行
- [バリデーション](#バリデーション) — ドメイン用語
- [バリデーションルール](#バリデーションルール) — ドメイン用語
- [ヒアリング](#ヒアリング) — ドメイン用語
- [ヒアリング結果](#ヒアリング結果) — ドメイン用語

### A-Z
- [ADB](#adb) — 略語
- [Answer](#answer) — データモデル
- [API Gateway](#api-gateway) — OCI用語
- [AppStatus](#appstatus) — データモデル
- [Container Instance](#container-instance) — OCI用語
- [DeployResult](#deployresult) — データモデル
- [Dynamic Group](#dynamic-group) — OCI用語
- [FastMCP](#fastmcp) — 技術用語
- [Galley](#galley) — ドメイン用語
- [HearingResult](#hearingresult) — データモデル
- [IaC](#iac) — 略語
- [MCP](#mcp) — 略語
- [MCPサーバー](#mcpサーバー) — 技術用語
- [MCPツール](#mcpツール) — 技術用語
- [MCPプロンプト](#mcpプロンプト) — 技術用語
- [MCPホスト](#mcpホスト) — 技術用語
- [MCPリソース](#mcpリソース) — 技術用語
- [OCI](#oci) — 略語
- [OCI SDK for Python](#oci-sdk-for-python) — 技術用語
- [OCIR](#ocir) — 略語
- [OKE](#oke) — 略語
- [Pydantic](#pydantic) — 技術用語
- [Resource Manager](#resource-manager) — 技術用語
- [SSE](#sse) — 略語
- [Terraform](#terraform) — 技術用語
- [TerraformResult](#terraformresult) — データモデル
- [ValidationResult](#validationresult) — データモデル
- [VCN](#vcn) — 略語
