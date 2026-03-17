# Components

## Component Overview

```
+------------------------------------------------------------------+
|  artifacts/                                                      |
|                                                                  |
|  +------------------------------------------------------------+ |
|  |  Skills (Markdown)                                          | |
|  |  - hearing.md          ヒアリング実行                       | |
|  |  - generate-terraform.md  Terraform生成                     | |
|  |  - deploy-infra.md     インフラ構築(RM)                     | |
|  |  - generate-app.md     アプリ生成                           | |
|  |  - deploy-app.md       アプリデプロイ                       | |
|  |  - verify.md           E2Eテスト                            | |
|  +------------------------------------------------------------+ |
|                                                                  |
|  +------------------------------------------------------------+ |
|  |  Workflows (Markdown)                                       | |
|  |  - build-demo-env.md   メインオーケストレーター             | |
|  +------------------------------------------------------------+ |
|                                                                  |
|  +------------------------------------------------------------+ |
|  |  Python Core Modules (src/)                                 | |
|  |  - oci_rm.py           Resource Manager操作                 | |
|  |  - oci_cli.py          OCI CLI ラッパー                     | |
|  |  - terraform_gen.py    Terraformテンプレート生成             | |
|  |  - deployer.py         コンテナビルド・デプロイ             | |
|  |  - e2e_runner.py       E2Eテスト実行                        | |
|  |  - reporter.py         進捗・結果レポート                   | |
|  +------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

## C-1: Hearing Skill (`hearing.md`)

- **Purpose**: ユーザーの自然言語要望から環境構築に必要な質問リストを生成し、回答を収集する
- **Type**: Claude Code Skill (Markdown)
- **Responsibilities**:
  - ユーザー要望の解析
  - 質問リストの動的生成（Markdown形式、AI-DLC方式）
  - 質問ファイルの作成（`hearing/questions.md`）
  - 回答の検証（矛盾検出、追加質問）
  - ヒアリング結果の構造化出力（`hearing/result.json`）
- **Interface**: 入力=自然言語テキスト、出力=構造化されたヒアリング結果

## C-2: Terraform Generator Skill (`generate-terraform.md`)

- **Purpose**: ヒアリング結果に基づきOCI Terraformコードを自動生成する
- **Type**: Claude Code Skill (Markdown) + Python Module
- **Responsibilities**:
  - ヒアリング結果の読み込みと解釈
  - OCIリソースのTerraformコード生成（Claude Codeの生成能力を活用）
  - Terraformベストプラクティスに従ったモジュール構成
  - `generated/{project-name}/terraform/` への出力
- **Interface**: 入力=ヒアリング結果、出力=Terraformファイル群

## C-3: Infrastructure Deployer Skill (`deploy-infra.md`)

- **Purpose**: OCI Resource Managerを使用してTerraformをapplyする
- **Type**: Claude Code Skill (Markdown) + Python Module (`oci_rm.py`)
- **Responsibilities**:
  - Terraformコードのzip圧縮
  - Resource Manager Stack作成（`oci resource-manager stack create`）
  - Plan実行・結果確認
  - Apply実行・ステータス監視
  - エラーハンドリング・リトライ
- **Interface**: 入力=Terraformディレクトリパス、出力=Stack OCID・リソース情報

## C-4: App Generator Skill (`generate-app.md`)

- **Purpose**: ヒアリング結果に基づきアプリケーションコードを自動生成する
- **Type**: Claude Code Skill (Markdown)
- **Responsibilities**:
  - ヒアリング結果に基づいたアプリケーション設計
  - アプリケーションコードの生成（Claude Codeの生成能力を活用）
  - Dockerfile / ビルド設定の生成
  - 単体テスト・結合テストの生成と実行
  - `generated/{project-name}/app/` への出力
- **Interface**: 入力=ヒアリング結果、出力=アプリケーションコード+テスト結果

## C-5: App Deployer Skill (`deploy-app.md`)

- **Purpose**: 生成したアプリケーションをOCI上にデプロイする
- **Type**: Claude Code Skill (Markdown) + Python Module (`deployer.py`)
- **Responsibilities**:
  - コンテナイメージのビルド
  - OCIRへのプッシュ
  - OKE / Container Instances / OCI Functionsへのデプロイ
  - デプロイ完了の確認
- **Interface**: 入力=アプリディレクトリパス+インフラ情報、出力=デプロイ結果（エンドポイントURL等）

## C-6: Verification Skill (`verify.md`)

- **Purpose**: デプロイしたアプリケーションの動作確認をE2Eテストで実行する
- **Type**: Claude Code Skill (Markdown) + Python Module (`e2e_runner.py`)
- **Responsibilities**:
  - ヘルスチェック（エンドポイント疎通確認）
  - 機能テスト（主要APIの動作確認）
  - テスト結果のレポート生成
  - 失敗時の診断情報収集
- **Interface**: 入力=エンドポイントURL+テスト仕様、出力=テスト結果レポート

## C-7: Main Workflow (`build-demo-env.md`)

- **Purpose**: 全フェーズを統括するメインオーケストレーターWorkflow
- **Type**: Claude Code Workflow (Markdown)
- **Responsibilities**:
  - フェーズ間の順序制御
  - 並行実行の管理（Resource Manager apply + App生成/テスト）
  - フェーズ間のデータ受け渡し
  - 全体進捗のレポート
  - エラー時のワークフロー中断・リカバリー判断
- **Interface**: 入力=ユーザーの自然言語要望、出力=完成したデモ環境情報

## C-8: OCI Resource Manager Module (`oci_rm.py`)

- **Purpose**: OCI Resource Manager操作のPythonラッパー
- **Type**: Python Module
- **Responsibilities**:
  - Stack作成（zipアップロード）
  - Plan Job実行・監視
  - Apply Job実行・監視
  - Stack/Jobステータスポーリング
  - ログ取得
- **Interface**: Python関数群（create_stack, run_plan, run_apply, get_status, get_logs）

## C-9: OCI CLI Wrapper (`oci_cli.py`)

- **Purpose**: OCI CLIコマンドの汎用Pythonラッパー
- **Type**: Python Module
- **Responsibilities**:
  - OCI CLIコマンドの実行と結果パース
  - JSON出力のパース
  - エラーハンドリング
  - コンパートメント・リージョン管理
- **Interface**: Python関数群（run_command, get_resource, list_resources）

## C-10: Deployer Module (`deployer.py`)

- **Purpose**: コンテナビルド・デプロイ操作のPythonモジュール
- **Type**: Python Module
- **Responsibilities**:
  - docker build / podman build 実行
  - OCIRへのイメージプッシュ
  - kubectl apply / OCI CLI によるデプロイ実行
  - デプロイステータス監視
- **Interface**: Python関数群（build_image, push_to_ocir, deploy_to_oke, deploy_to_ci, deploy_to_functions）

## C-11: E2E Test Runner (`e2e_runner.py`)

- **Purpose**: E2Eテスト実行エンジン
- **Type**: Python Module
- **Responsibilities**:
  - HTTP/HTTPSヘルスチェック
  - APIエンドポイントテスト
  - レスポンス検証
  - テスト結果の構造化出力
- **Interface**: Python関数群（health_check, test_endpoint, run_test_suite, generate_report）

## C-12: Reporter Module (`reporter.py`)

- **Purpose**: 進捗・結果レポート生成
- **Type**: Python Module
- **Responsibilities**:
  - フェーズ進捗のMarkdownレポート生成
  - 最終結果サマリー生成（環境URL、リソース一覧、Stack OCID等）
  - エラーレポート生成
- **Interface**: Python関数群（report_progress, generate_summary, report_error）
