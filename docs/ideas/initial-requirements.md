# Galley 設計書

## 1. プロジェクト概要

### 背景

Oracle Cloud Infrastructure（OCI）のプリセールスエンジニアとして、技術検証やソリューション確立（既存サービスの組み合わせ）を日常的に行っている。これらの技術的作業をAI（Claude）で加速するためのシステム「Galley」を構築する。

### Galleyとは

GalleyはPython + FastMCPで実装するOCIプリセールス支援MCPサーバーである。利用者はClaude Desktop / claude.ai等のMCPホストからGalleyに接続し、要件のヒアリングからアーキテクチャ設計、インフラ構築、アプリケーションデプロイまでを一貫して行える。

### 解決する課題

- 技術検証のイテレーションが遅い（Terraform生成 → 手動apply → エラー → 手動修正の繰り返し）
- 各利用者の環境差異（OCI CLI、Terraform等のセットアップ）による導入障壁
- 設計知識やソリューションパターンの属人化
- インフラ構築後のアプリケーションデプロイまでの手作業

---

## 2. 技術スタック

| 領域 | 技術 |
|---|---|
| MCPサーバーフレームワーク | FastMCP（Python） |
| OCI操作 | OCI CLI、OCI SDK for Python |
| IaC | Terraform + OCI Provider |
| コンテナオーケストレーション | kubectl |
| コンテナランタイム | OCI Container Instances |
| 認証（OCI） | Resource Principal |
| 認証（MCPエンドポイント） | URLトークン + API Gateway |
| データ永続化 | OCI Object Storage |
| CI/CD連携 | OCI DevOps |

---

## 3. アーキテクチャ

### 全体構成

```
利用者のPC（Claude Desktop / claude.ai）
  └─ MCP接続（HTTPS / SSE or StreamableHTTP）
       └─ OCI API Gateway（HTTPS終端 + URLトークン認証）
            └─ OCI Container Instance（プライベートサブネット）
                 ├─ Galley MCPサーバー（Python / FastMCP）
                 ├─ OCI CLI + OCI SDK for Python（Resource Principal認証）
                 ├─ Terraform + OCI Provider
                 ├─ kubectl
                 └─ Object Storage連携
                      ├─ Terraform state
                      ├─ セッションデータ
                      ├─ テンプレートストア
                      └─ バリデーションルール
```

### 設計方針

- **MCPサーバーに機能を集約する：** 利用者のローカル環境にOCI CLIやTerraform等のセットアップを不要にする
- **コンテナイメージとして配布する：** 環境差異を排除する
- **OCIサービスに重い処理を委譲する：** Galleyコンテナ自体は軽量なオーケストレーション層に留める
- **データをObject Storageで管理する：** テンプレートやバリデーションルールを開発者が随時追加・更新できる構造にする
- **OCI SDK for Pythonを活用する：** OCI CLIのラッパーに加え、SDK直接呼び出しでより柔軟なOCI操作を実現する

### 配布形態

- **コンテナイメージ：** OCIRのパブリックリポジトリに配置（タグでバージョン管理）
- **インフラ構成：** Terraformファイルとして配布

### 利用者の導入手順

1. Terraformファイルを入手
2. 変数を設定（`compartment_id`、`region`等）
3. `terraform apply` を実行
4. 出力されたMCPエンドポイントURL（トークン付き）をMCPホストに設定

---

## 4. 機能の全体像

```
Galleyの機能層

1. ヒアリング層 — 要件を構造化する

2. 設計層
   ├─ 自動設計モード — ヒアリング結果から推奨構成を提案
   └─ 対話型設計モード — 利用者主導で構成を組み立て
        ├─ コンポーネントの追加・削除・設定変更
        ├─ 構成バリデーション（OCI固有の制約チェック）
        └─ 構成図のリアルタイム更新

3. インフラ層 — Terraform生成・実行・デバッグ

4. アプリケーション層 — テンプレート + カスタマイズ + デプロイ

横断的な基盤
├─ テンプレートストア（Object Storage、開発者が追加可能）
├─ バリデーションルール（Object Storage、開発者が追加可能）
└─ セッション・state管理（Object Storage）
```

---

## 5. Terraformで作成するリソース（配布用）

利用者が `terraform apply` を実行すると、以下のリソースが作成される。

| リソース | 用途 |
|---|---|
| Container Instance | Galley MCPサーバーの実行環境（OCIRからイメージをpull） |
| API Gateway + Deployment | HTTPS終端、URLトークン認証、MCPエンドポイントの公開 |
| Object Storage Bucket | Terraform state、セッションデータ、テンプレート、バリデーションルール |
| VCN / Subnet / Security List | ネットワーク構成 |
| Dynamic Group | Container InstanceをResource Principal認証の対象にする |
| IAM Policy | Dynamic Groupに対するリソース操作権限の付与 |

### 利用者が入力する変数

| 変数名 | 説明 |
|---|---|
| `compartment_id` | Galleyインフラのデプロイ先コンパートメント |
| `region` | OCIリージョン |
| `galley_work_compartment_id` | Galleyが検証リソースを作成するコンパートメント（任意、デフォルトは`compartment_id`と同じ） |
| `image_tag` | コンテナイメージのバージョンタグ（任意、デフォルトは`latest`） |

---

## 6. MCPツール一覧

### ヒアリング層

| ツール名 | 機能 |
|---|---|
| `galley:create_session` | ヒアリングセッションの作成 |
| `galley:save_answer` / `save_answers_batch` | ヒアリング回答の保存 |
| `galley:complete_hearing` | ヒアリングの完了 |
| `galley:get_hearing_result` | ヒアリング結果の取得 |

### 設計層 — 自動設計モード

| ツール名 | 機能 |
|---|---|
| `galley:save_architecture` | 推奨アーキテクチャの保存 |

### 設計層 — 対話型設計モード

| ツール名 | 機能 |
|---|---|
| `galley:add_component` | アーキテクチャにコンポーネントを追加 |
| `galley:remove_component` | コンポーネントを削除 |
| `galley:configure_component` | コンポーネントの詳細設定を変更（シェイプ、ネットワーク構成等） |
| `galley:validate_architecture` | 現在の構成を検証し、問題点や推奨事項を返す |
| `galley:list_available_services` | 追加可能なOCIサービス一覧とその説明を返す |

### インフラ層 — ローカルTerraform実行

| ツール名 | 機能 |
|---|---|
| `galley:run_terraform_plan` | terraform planを実行し、結果（成功 or エラー詳細）を返す |
| `galley:run_terraform_apply` | terraform applyを実行する |
| `galley:run_terraform_destroy` | terraform destroyを実行し、検証リソースをクリーンアップする |

### インフラ層 — Resource Manager連携

| ツール名 | 機能 |
|---|---|
| `galley:create_rm_stack` | Resource Managerスタックの作成 |
| `galley:run_rm_plan` | Planジョブの実行 |
| `galley:run_rm_apply` | Applyジョブの実行 |
| `galley:get_rm_job_status` | ジョブ状態・ログの取得 |

### インフラ層 — OCI操作

| ツール名 | 機能 |
|---|---|
| `galley:run_oci_cli` | 任意のOCI CLIコマンドを実行し、結果を返す |
| `galley:oci_sdk_call` | OCI SDK for Pythonを利用したAPI呼び出し（構造化された入出力） |

### アプリケーション層

| ツール名 | 機能 |
|---|---|
| `galley:list_templates` | 利用可能なテンプレート一覧を返す |
| `galley:scaffold_from_template` | テンプレートからプロジェクトを生成（パラメータ付き） |
| `galley:update_app_code` | 生成済みアプリコードの一部を更新（LLMによるカスタマイズ用） |
| `galley:build_and_deploy` | ビルド → OCIR push → OKEデプロイを一括実行 |
| `galley:check_app_status` | デプロイ状態・ログ・ヘルスチェック結果を返す |

### エクスポート

| ツール名 | 機能 |
|---|---|
| `galley:export_summary` | 要件サマリーをMarkdownで出力 |
| `galley:export_mermaid` | 構成図をMermaidで出力 |
| `galley:export_iac` | IaCテンプレートを出力 |
| `galley:export_all` | 全成果物を一括出力 |

---

## 7. 設計層の詳細

### 自動設計モード

- ヒアリング結果からGalleyが推奨アーキテクチャを提案する
- 初期案をサッと作りたいとき、詳しくない領域の参考にしたいとき向け

### 対話型設計モード

- 利用者がアーキテクチャを主導で組み立て、Galleyが支援する
- 利用者が「OKE + ADB + API Gatewayで行く」と指定 → Galleyが受け入れて構成を組み立て
- 各コンポーネントの詳細設定を対話的に詰められる
- 利用者の設計判断に対してフィードバックを返す（例：「この構成だとOKEからADBにPrivate Endpointが必要です」）
- 構成図をリアルタイムに更新しながら進められる

### バリデーションルール

`validate_architecture` の精度を上げるため、OCI固有の制約知識をデータとして管理する：

- サービス間の接続要件（例：OKEからADBはPrivate Endpointが必要）
- リージョン別のサービス可用性
- シェイプの制約やサービスリミットの一般的な値
- ネットワーク構成のベストプラクティス

これらはObject Storage上にJSON/YAML等で管理し、Galley開発者が随時追加・更新できる構造とする。

---

## 8. インフラ層の詳細

### 自動デバッグループ

LLM側がデバッグの判断・修正を行い、MCPサーバーは実行のみを担当する。

```
1. LLMがTerraformファイルを生成
2. galley:run_terraform_plan を呼び出し
3. エラーがあればLLMがエラーメッセージを解析
4. LLMがTerraformファイルを修正
5. 再度 galley:run_terraform_plan を呼び出し
6. 成功したら galley:run_terraform_apply を実行
```

### ローカルTerraform実行 vs Resource Manager連携の棲み分け

| 項目 | ローカルTerraform実行 | Resource Manager連携 |
|---|---|---|
| 用途 | 検証・デバッグ | 本番デプロイ、顧客への引き渡し |
| 実行環境 | Galleyコンテナ内 | OCI Resource Manager |
| イテレーション速度 | 高速（即時実行） | 低速（ジョブキュー経由） |
| state管理 | Object Storage（Galley管理） | Resource Manager管理 |

---

## 9. アプリケーション層の詳細

### テンプレート + カスタマイズの二層構造

**テンプレートが出発点、LLMによるカスタマイズがオプション**という設計。

利用フロー例：

```
1. 「OKE上にREST APIとAutonomous Databaseの構成を作りたい」
2. → galley:list_templates で利用可能なテンプレートを確認
3. → galley:scaffold_from_template でベースのアプリとインフラを生成
4. → 「APIのエンドポイントにこういうロジックを追加したい」
5. → galley:update_app_code でLLMがテンプレートをカスタマイズ
6. → galley:build_and_deploy でビルド・デプロイ
7. → galley:check_app_status で動作確認
8. → エラーがあればLLMが修正して再デプロイ
```

### テンプレートストアの構造

```
Object Storage Bucket
└─ templates/
     ├─ rest-api-adb/               # REST API + Autonomous Database
     │    ├─ app/                    # アプリケーションコード
     │    ├─ k8s/                    # Kubernetesマニフェスト
     │    ├─ terraform/              # インフラ定義
     │    └─ template.json           # メタデータ
     ├─ frontend-oke/                # フロントエンド on OKE
     ├─ fn-event-driven/             # Oracle Functions + Streaming
     └─ ...（開発者が随時追加可能）
```

`template.json` にカスタマイズ可能なポイント（DBスキーマ、APIエンドポイント定義、環境変数など）を定義。ヒアリングフローで利用者から聞き出して反映する。

テンプレートの追加は、所定のディレクトリ構造と `template.json` の仕様に従ってObject Storageにアップロードするだけで完了する設計とする。

### ビルド・デプロイの実行方式

Galleyコンテナ自体を軽量に保つため、**OCIサービスにビルド・デプロイ処理を委譲**する：

- ビルド → OCI DevOpsビルドパイプライン
- イメージ格納 → OCIR
- デプロイ → OKE API / kubectl

Galleyの役割はこれらのOCIサービスのオーケストレーションであり、重い処理はOCI側が担当する。

### カスタマイズ時の安全策

- カスタマイズ前のコードをObject Storageにスナップショット保存し、ロールバック可能にする
- `build_and_deploy` の後にヘルスチェックを自動実行し、疎通不可なら自動ロールバック
- テンプレートのコア部分（DB接続設定、認証周り等）はカスタマイズ不可とマーク可能にする

---

## 10. 認証・セキュリティ設計

### OCI認証

- **Resource Principal認証**を使用
- Container InstanceがDynamic Groupに含まれ、IAM PolicyによりOCIリソースの操作権限を取得
- OCI SDK for PythonのResource Principal Providerを利用
- APIキーの配布・管理が不要

### MCPエンドポイントの認証

- IdPが利用できない環境を前提とし、**URLトークン認証**を採用
- `https://<api-gateway-endpoint>/mcp?token=<ランダム文字列>` の形式
- トークンは `terraform apply` 時にランダム生成し、Terraform outputとして出力
- API GatewayがHTTPS終端を担当するため、利用者側でのドメイン取得・証明書管理は不要
- 将来IdPが利用可能になった場合、OAuth認証への切り替えを検討

### 権限の分離

- IAM Policyで操作対象を `galley_work_compartment_id` 内に限定
- Galley自体のインフラ（Container Instance、API Gateway等）に影響を及ぼさない設計
- 利用者のサービスリミットが追加の安全装置として機能

---

## 11. 開発フェーズ

### Phase 1：MCPサーバーの基盤構築

- Python + FastMCPによるMCPサーバーの実装
- SSE / StreamableHTTPエンドポイントの設定
- Dockerfileの作成（Python、OCI CLI、OCI SDK for Python、Terraform、kubectl を含む）
- トークン認証の実装
- ヒアリング層のMCPツール実装（create_session、save_answer等）

### Phase 2：配布基盤の構築

- 配布用Terraformの作成（Container Instance、API Gateway、Object Storage、VCN、IAM等）
- OCIRへのコンテナイメージ公開
- `terraform apply` → MCP接続の一連のフローの検証

### Phase 3：設計層の実装

- 自動設計モードの実装（save_architecture）
- 対話型設計モードの実装（add / remove / configure component）
- `validate_architecture` の実装
- バリデーションルールのデータ構造設計とObject Storage管理
- エクスポート機能の実装（Markdown、Mermaid、IaC）

### Phase 4：インフラ層の実装

- OCI SDK for PythonによるResource Principal認証の実装
- OCI CLI実行ツール / OCI SDK呼び出しツールの実装
- Terraform実行ツール群の実装（plan / apply / destroy）
- Object StorageへのTerraform state保存
- Resource Manager連携ツールの実装（OCI SDKを利用）

### Phase 5：アプリケーション層の実装

- テンプレートストアの構造設計とObject Storage管理
- テンプレート関連MCPツールの実装（list / scaffold / update）
- OCI DevOps連携によるビルド・デプロイパイプラインの実装（Terraformで対応できない場合はOCI SDKを利用）
- デプロイ状態確認・自動ロールバックの実装
- 初期テンプレートの作成

### 将来構想

- ソリューションパターンのナレッジベース構築
- 検証結果の自動ドキュメント化
- チーム全体でのナレッジ共有機能
- バリデーションルールの自動学習（検証結果からのフィードバック）