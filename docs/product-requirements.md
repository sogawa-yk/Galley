# プロダクト要求定義書 (Product Requirements Document)

## プロダクト概要

### 名称
**Galley** - OCI プリセールス支援 MCP サーバー

### プロダクトコンセプト
- **AI駆動のOCIソリューション構築**: Claude等のLLMからMCP経由でOCIリソースの設計・構築・デプロイを一貫して実行できる
- **ゼロセットアップ利用体験**: OCI CLI、Terraform、kubectl等のツールをコンテナに集約し、利用者のローカル環境にセットアップ不要
- **拡張可能なナレッジベース**: テンプレートやバリデーションルールをObject Storageで管理し、開発者が随時追加・更新できる

### プロダクトビジョン
OCIプリセールスエンジニアが技術検証やソリューション確立の速度を飛躍的に向上させるためのAI支援プラットフォームを提供する。利用者はClaude Desktop等のMCPホストからGalleyに接続するだけで、要件のヒアリングからアーキテクチャ設計、インフラ構築、アプリケーションデプロイまでを対話的に一貫して行える。設計知識やソリューションパターンの属人化を解消し、チーム全体の技術力を底上げする。

### 目的
- 技術検証のイテレーションを高速化する（Terraform生成→apply→エラー修正の自動デバッグループ）
- 利用者の環境差異による導入障壁を排除する（コンテナイメージとして配布）
- 設計知識・ソリューションパターンをデータとして蓄積・共有する
- インフラ構築後のアプリケーションデプロイまでの手作業を削減する

## ターゲットユーザー

### プライマリーペルソナ: 山田健一（32歳、OCIプリセールスエンジニア）
- OCI歴3年、顧客向けの技術検証やソリューション提案を担当
- 週に2〜3件の検証案件を並行で対応
- OCI CLIやTerraformは使えるが、毎回のセットアップや細かいパラメータ調整に時間を取られている
- 顧客からの要件ヒアリング後、検証環境の構築に半日〜1日かかることがある
- **現在の課題**: 検証イテレーションが遅く、Terraformエラーの手動修正に時間を浪費している
- **期待する解決策**: AIとの対話だけで要件整理からインフラ構築・アプリデプロイまで完了させたい
- **1日の典型的なワークフロー**: 午前に顧客ミーティング → 午後に検証環境構築 → 夕方にデモ準備

### セカンダリーペルソナ: 佐藤美咲（27歳、OCIジュニアエンジニア）
- OCI歴1年未満、先輩エンジニアの支援のもとで検証作業を実施
- OCIの各サービスの組み合わせ方や制約に不慣れ
- **現在の課題**: どのサービスをどう組み合わせるべきか判断できず、都度先輩に相談している
- **期待する解決策**: ベストプラクティスに基づいた設計提案を受けながら自律的に検証を進めたい
- **1日の典型的なワークフロー**: タスクアサイン後に先輩に相談 → Galleyのヒアリングと自動設計でサービス構成を把握 → バリデーション結果を確認しながら設計調整
- **主に使う機能**: F4（自動設計モード）、F6（アーキテクチャバリデーション）、F5（対話型設計モード）

## 成功指標（KPI）

### プライマリーKPI
- 検証環境の構築時間: 従来の半日〜1日 → 1〜2時間以内（3ヶ月後）
  - 計測方法: Session.created_at から `terraform apply` 成功時刻までの差分をObject Storageログから集計
  - 計測タイミング: Phase 4（F8）実装から1ヶ月後、その後月次モニタリング
- Terraformエラーの自動解決率: 80%以上（apply成功までの自動デバッグループ完了率）
  - 計測方法: セッションごとの `terraform plan` 失敗回数と最終的な `terraform apply` 成功/失敗を集計
  - 計測タイミング: Phase 4（F8）実装から1ヶ月後、その後月次モニタリング
- `terraform apply` 実行時に利用者によるTerraformコード手動修正が不要なケース: 90%以上
  - 計測方法: LLMによる自動修正のみで apply 成功した件数 / 全 apply 試行件数
  - 計測タイミング: Phase 4（F8）実装から1ヶ月後、その後月次モニタリング

### セカンダリーKPI
- 利用者がヒアリング〜アーキテクチャ設計完了まで要する時間: 30分以内
  - 計測方法: Session.created_at から Architecture保存時の Session.updated_at までの差分
- テンプレートからのアプリケーションデプロイ成功率: 95%以上
  - 計測方法: `build_and_deploy` の成功件数 / 全実行件数（ロールバック発生は失敗としてカウント）
- バリデーションルールによる設計上の問題の事前検出率: 70%以上
  - 計測方法: `validate_architecture` で検出された問題のうち、後続の Terraform plan/apply エラーに対応するもの

## 機能要件

### コア機能（MVP） — Phase 1: MCPサーバー基盤 + ヒアリング層

#### F1: MCPサーバー基盤

**ユーザーストーリー**:
プリセールスエンジニアとして、Claude DesktopからGalleyに接続するために、SSE/StreamableHTTP対応のMCPサーバーが欲しい

**受け入れ条件**:
- [ ] Python + FastMCPで実装されたMCPサーバーが起動し、MCPホストから接続できる
- [ ] SSEまたはStreamableHTTPでのMCP通信が正常に動作する
- [ ] Dockerfileにより、Python、OCI CLI、OCI SDK for Python、Terraform、kubectlを含むコンテナイメージがビルドできる
- [ ] Resource Principal認証によるOCI操作が可能

**優先度**: P0（必須）

#### F2: ヒアリングセッション管理

**ユーザーストーリー**:
プリセールスエンジニアとして、顧客の要件を構造化するために、対話的なヒアリングセッションを作成・管理したい

**受け入れ条件**:
- [ ] `galley:create_session` でヒアリングセッションを作成できる
- [ ] `galley:save_answer` / `galley:save_answers_batch` で回答を保存できる
- [ ] `galley:complete_hearing` でヒアリングを完了し、結果を構造化できる
- [ ] `galley:get_hearing_result` でヒアリング結果を取得できる
- [ ] セッションデータがObject Storageに永続化される

**優先度**: P0（必須）

### コア機能（MVP） — Phase 2: 配布基盤

#### F3: 配布用Terraformとコンテナイメージ

**ユーザーストーリー**:
プリセールスエンジニアとして、`terraform apply` 一発でGalley環境を構築するために、配布用Terraformとコンテナイメージが欲しい

**受け入れ条件**:
- [ ] 配布用TerraformでContainer Instance、API Gateway、Object Storage、VCN、IAM等が自動作成される
- [ ] 利用者が入力する変数は `compartment_id`、`region`、`galley_work_compartment_id`（任意）、`image_tag`（任意）のみ
- [ ] `terraform apply` 完了後、MCP接続用のURLトークン付きエンドポイントがoutputとして出力される
- [ ] OCIRのパブリックリポジトリにコンテナイメージが公開されている
- [ ] API GatewayがHTTPS終端とURLトークン認証を提供する

**優先度**: P0（必須）

### コア機能 — Phase 3: 設計層

#### F4: 自動設計モード

**ユーザーストーリー**:
プリセールスエンジニアとして、ヒアリング結果から推奨アーキテクチャの初期案を素早く得るために、自動設計機能が欲しい

**受け入れ条件**:
- [ ] LLMがヒアリング結果（`galley:get_hearing_result` の返却値）を分析し、推奨アーキテクチャを構成する（Galleyはプロンプトと保存ツールを提供）
- [ ] `galley:save_architecture` で生成されたアーキテクチャを保存できる
- [ ] 生成されたアーキテクチャにはコンポーネント一覧、接続関係、推奨理由が含まれる

**優先度**: P0（必須）

#### F5: 対話型設計モード

**ユーザーストーリー**:
プリセールスエンジニアとして、自分の知識と判断でアーキテクチャを組み立てるために、コンポーネントの追加・削除・設定変更を対話的に行いたい

**受け入れ条件**:
- [ ] `galley:add_component` でアーキテクチャにコンポーネントを追加できる
- [ ] `galley:remove_component` でコンポーネントを削除できる
- [ ] `galley:configure_component` でコンポーネントの詳細設定（シェイプ、ネットワーク構成等）を変更できる
- [ ] `galley:list_available_services` で追加可能なOCIサービス一覧を取得できる
- [ ] 利用者の設計判断に対してフィードバックを返す（例：「OKEからADBにPrivate Endpointが必要」）

**優先度**: P0（必須）

#### F6: アーキテクチャバリデーション

**ユーザーストーリー**:
プリセールスエンジニアとして、設計ミスを事前に検出するために、OCI固有の制約に基づく構成バリデーションが欲しい

**受け入れ条件**:
- [ ] `galley:validate_architecture` で現在の構成を検証し、問題点と推奨事項のリストを返す
- [ ] サービス間の接続要件（例：Private Endpoint必要性）を検出できる
- [ ] リージョン別のサービス可用性を考慮した検証ができる
- [ ] バリデーションルールはYAML形式でリポジトリの `config/validation-rules/` にマスター管理され、本番環境ではObject Storageに同期される。開発者がルールを追加・更新できる

**優先度**: P0（必須）

#### F7: エクスポート機能

**ユーザーストーリー**:
プリセールスエンジニアとして、設計成果を顧客やチームに共有するために、Markdown・Mermaid・IaCの各形式でエクスポートしたい

**受け入れ条件**:
- [ ] `galley:export_summary` で要件サマリーをMarkdownで出力できる
- [ ] `galley:export_mermaid` で構成図をMermaid形式で出力できる
- [ ] `galley:export_iac` でIaCテンプレート（Terraform）を出力できる
- [ ] `galley:export_all` で全成果物を一括出力できる

**優先度**: P1（重要）

### コア機能 — Phase 4: インフラ層

#### F8: ローカルTerraform実行

**ユーザーストーリー**:
プリセールスエンジニアとして、検証環境を素早く構築・破棄するために、Galleyコンテナ内でTerraformを直接実行したい

**受け入れ条件**:
- [ ] `galley:run_terraform_plan` でplan結果（成功またはエラー詳細）を返す
- [ ] `galley:run_terraform_apply` でapplyを実行できる
- [ ] `galley:run_terraform_destroy` でリソースをクリーンアップできる
- [ ] Terraform stateがObject Storageに保存される
- [ ] LLMがエラーメッセージを解析→Terraform修正→再実行の自動デバッグループが機能する

**優先度**: P0（必須）

#### F9: OCI操作ツール

**ユーザーストーリー**:
プリセールスエンジニアとして、Terraformでカバーしきれない柔軟なOCI操作を行うために、OCI CLIとSDKの実行手段が欲しい

**受け入れ条件**:
- [ ] `galley:run_oci_cli` で任意のOCI CLIコマンドを実行し、結果を返す
- [ ] `galley:oci_sdk_call` でOCI SDK for Pythonを利用した構造化API呼び出しができる
- [ ] Resource Principal認証により、APIキー配布なしでOCI操作が可能

**優先度**: P0（必須）

#### F10: Resource Manager連携

**ユーザーストーリー**:
プリセールスエンジニアとして、本番デプロイや顧客引き渡し用の構成を管理するために、OCI Resource Managerと連携したい

**受け入れ条件**:
- [ ] `galley:create_rm_stack` でResource Managerスタックを作成できる
- [ ] `galley:run_rm_plan` でPlanジョブを実行できる
- [ ] `galley:run_rm_apply` でApplyジョブを実行できる
- [ ] `galley:get_rm_job_status` でジョブ状態とログを取得できる

**優先度**: P1（重要）

### コア機能 — Phase 5: アプリケーション層

#### F11: テンプレートストア

**ユーザーストーリー**:
プリセールスエンジニアとして、検証で頻繁に使うアプリケーション構成を再利用するために、テンプレートストアが欲しい

**受け入れ条件**:
- [ ] `galley:list_templates` で利用可能なテンプレート一覧（名称、説明、カスタマイズポイント）を返す
- [ ] `galley:scaffold_from_template` でテンプレートからプロジェクトを生成できる（パラメータ付き）
- [ ] テンプレートはObject Storageの所定のディレクトリ構造に従い、`template.json` でメタデータを定義
- [ ] 開発者がテンプレートを随時追加・更新できる

**優先度**: P1（重要）

#### F12: アプリケーションカスタマイズとデプロイ

**ユーザーストーリー**:
プリセールスエンジニアとして、テンプレートから生成したアプリを顧客要件に合わせて調整し、ワンコマンドでデプロイするために、カスタマイズとデプロイ機能が欲しい

**受け入れ条件**:
- [ ] `galley:update_app_code` でLLMによるアプリコードのカスタマイズができる
- [ ] `galley:build_and_deploy` でビルド→OCIR push→OKEデプロイを一括実行できる
- [ ] `galley:check_app_status` でデプロイ状態・ログ・ヘルスチェック結果を返す
- [ ] カスタマイズ前のコードがObject Storageにスナップショット保存され、ロールバック可能
- [ ] デプロイ後のヘルスチェック失敗時に自動ロールバックが動作する
- [ ] テンプレートのコア部分（DB接続設定、認証周り等）はカスタマイズ不可とマーク可能

**優先度**: P1（重要）

### MCPツールインターフェース

```
# ヒアリング層
galley:create_session          — ヒアリングセッションの作成
galley:save_answer             — ヒアリング回答の保存（単件）
galley:save_answers_batch      — ヒアリング回答の保存（バッチ）
galley:complete_hearing        — ヒアリングの完了
galley:get_hearing_result      — ヒアリング結果の取得

# 設計層（自動設計）
galley:save_architecture       — 推奨アーキテクチャの保存

# 設計層（対話型設計）
galley:add_component           — コンポーネントの追加
galley:remove_component        — コンポーネントの削除
galley:configure_component     — コンポーネントの設定変更
galley:validate_architecture   — 構成バリデーション
galley:list_available_services — 利用可能サービス一覧

# インフラ層（ローカルTerraform）
galley:run_terraform_plan      — terraform plan実行
galley:run_terraform_apply     — terraform apply実行
galley:run_terraform_destroy   — terraform destroy実行

# インフラ層（Resource Manager）
galley:create_rm_stack         — RMスタック作成
galley:run_rm_plan             — Planジョブ実行
galley:run_rm_apply            — Applyジョブ実行
galley:get_rm_job_status       — ジョブ状態取得

# インフラ層（OCI操作）
galley:run_oci_cli             — OCI CLIコマンド実行
galley:oci_sdk_call            — OCI SDK API呼び出し

# アプリケーション層
galley:list_templates          — テンプレート一覧
galley:scaffold_from_template  — テンプレートからプロジェクト生成
galley:update_app_code         — アプリコード更新
galley:build_and_deploy        — ビルド・デプロイ一括実行
galley:check_app_status        — デプロイ状態確認

# エクスポート
galley:export_summary          — 要件サマリー（Markdown）
galley:export_mermaid          — 構成図（Mermaid）
galley:export_iac              — IaCテンプレート出力
galley:export_all              — 全成果物一括出力
```

### 将来的な機能（Post-MVP）

#### ソリューションパターンのナレッジベース

検証結果や成功パターンを蓄積し、チーム全体で参照可能なナレッジベースを構築する。

**優先度**: P2（できれば）

#### 検証結果の自動ドキュメント化

検証プロセスと結果を自動的にドキュメント化し、顧客への報告書作成を効率化する。

**優先度**: P2（できれば）

#### バリデーションルールの自動学習

検証結果からのフィードバックを基に、バリデーションルールを自動的に改善する。

**優先度**: P2（できれば）

#### OAuth認証への切り替え

IdPが利用可能な環境向けに、URLトークン認証からOAuth認証への移行オプションを提供する。

**優先度**: P2（できれば）

## 非機能要件

### パフォーマンス
- MCPツール呼び出しのレスポンス開始: 3秒以内（Terraform実行等の長時間処理を除く）
- `terraform plan` の実行結果返却: リソース数に依存するが、10リソース以下の構成で60秒以内
- ヒアリングセッションのCRUD操作: 1秒以内
- Object Storageへのデータ読み書き: 2秒以内

### ユーザビリティ
- 利用者は `terraform apply` + MCPホスト設定の2ステップで利用開始できる
- MCPツールの命名とパラメータが直感的であること（受け入れ条件: 統合テストにてLLMが正しいツールを1回目の呼び出しで選択できるシナリオを3件以上定義し、全件パス）
- エラーメッセージはJSON構造化形式で返し、`error`フィールド（エラー種別）と `message`フィールド（説明）を必ず含むこと（受け入れ条件: 機能設計書のエラー分類表に従った実装であること）

### 信頼性
- セッションデータの永続化: 変更の都度Object Storageに即時書き込みし、コンテナクラッシュ時のデータ損失を最小化（最後の書き込み以降のメモリ上キャッシュは損失する可能性がある）
- Terraform state の整合性: 同時実行による競合を防止
- アプリケーションデプロイ失敗時の自動ロールバック成功率: 95%以上

### セキュリティ
- OCI認証: Resource Principal認証のみ使用し、APIキーをコンテナに保持しない
- MCPエンドポイント認証: API GatewayによるHTTPS終端 + URLトークン認証
- 権限分離: Galleyの操作対象を `galley_work_compartment_id` 内に限定するIAM Policy
- Galley自体のインフラ（Container Instance、API Gateway等）への操作権限を持たない設計
- テンプレートのコア部分（DB接続設定、認証周り）のカスタマイズ保護

### スケーラビリティ
- 単一コンテナインスタンスでの利用を前提（プリセールスチームの少人数利用）
- テンプレートストアとバリデーションルールはObject Storageで管理し、容量制限なし
- 将来的なマルチテナント対応は現時点ではスコープ外

## スコープ外

明示的にスコープ外とする項目:
- マルチテナント対応（複数チームでの共用）
- GUIダッシュボード（すべてMCPホスト経由の対話で操作）
- OCI以外のクラウドプロバイダー対応
- 本番運用環境の継続的な監視・運用管理
- 利用者のローカル環境でのTerraform/OCI CLI実行支援
- OCI以外の認証方式（OAuth等）の初期サポート（将来構想として記載）
