# Application Design - Consolidated

## Architecture Overview

OCI上でデモ環境・検証環境を自然言語から自動構築するClaude Code Skills/Workflowsシステム。

### 設計原則
- **定型処理はPython**: OCI操作、ビルド、テスト実行はPythonモジュール
- **創造的処理はSkill**: ヒアリング質問生成、アプリコード生成はClaude Codeの能力を活用
- **WorkflowはオーケストレーターのみFinally**: フェーズ順序制御と並行実行管理に専念
- **ファイルシステムでデータ受け渡し**: Skill間はJSON/Markdownファイルで連携

### ディレクトリ構成

```
artifacts/                          # 開発成果物
  skills/                           # Claude Code Skills
    hearing.md
    generate-terraform.md
    deploy-infra.md
    generate-app.md
    deploy-app.md
    verify.md
  workflows/                        # Claude Code Workflows
    build-demo-env.md
  src/                              # Python Core Modules
    oci_rm.py
    oci_cli.py
    deployer.py
    e2e_runner.py
    reporter.py
    __init__.py
  tests/                            # Python Tests
    test_oci_rm.py
    test_oci_cli.py
    test_deployer.py
    test_e2e_runner.py
    test_reporter.py
  pyproject.toml                    # uv package management

generated/                          # 実行時生成物（gitignore対象）
  {project-name}/
    terraform/                      # 生成されたTerraformコード
    app/                            # 生成されたアプリケーションコード
    hearing/                        # ヒアリング関連ファイル
      questions.md
      result.json
    stack_outputs.json              # RM apply結果
    endpoints.json                  # デプロイ先エンドポイント
    test_results.json               # E2Eテスト結果
    summary.md                      # 最終レポート
```

### Workflow実行フロー

```
User: "Eコマースのデモ環境を作って"
      |
      v
[1. Hearing Phase]
      | hearing.md が質問生成・回答収集
      | -> hearing/result.json
      v
[2. Terraform Generation]
      | generate-terraform.md がTFコード生成
      | -> generated/{name}/terraform/
      v
[3. Parallel Execution]
      |
      +-- [3a. Infrastructure]         [3b. App Generation]
      |   deploy-infra.md              generate-app.md
      |   oci_rm.py (Stack+Apply)      アプリコード生成
      |   (数分〜数十分)               単体テスト・結合テスト
      |                                (数分)
      +-- 両方完了を待機 ---------------+
      |
      v
[4. App Deploy]
      | deploy-app.md
      | deployer.py (build, push, deploy)
      v
[5. Verification]
      | verify.md
      | e2e_runner.py (health check, API test)
      v
[6. Report]
      | reporter.py (summary.md生成)
      | ユーザーに結果報告
```

### コンポーネント一覧

| ID | Name | Type | Purpose |
|---|---|---|---|
| C-1 | hearing.md | Skill | ヒアリング質問生成・回答収集 |
| C-2 | generate-terraform.md | Skill | Terraformコード自動生成 |
| C-3 | deploy-infra.md | Skill+Python | Resource Manager経由インフラ構築 |
| C-4 | generate-app.md | Skill | アプリケーションコード自動生成 |
| C-5 | deploy-app.md | Skill+Python | アプリビルド・デプロイ |
| C-6 | verify.md | Skill+Python | E2Eテスト・動作確認 |
| C-7 | build-demo-env.md | Workflow | メインオーケストレーター |
| C-8 | oci_rm.py | Python | Resource Manager操作 |
| C-9 | oci_cli.py | Python | OCI CLI汎用ラッパー |
| C-10 | deployer.py | Python | ビルド・デプロイ操作 |
| C-11 | e2e_runner.py | Python | E2Eテスト実行 |
| C-12 | reporter.py | Python | レポート生成 |

### 詳細設計ドキュメント参照
- [components.md](components.md) - コンポーネント定義・責務
- [component-methods.md](component-methods.md) - メソッドシグネチャ
- [services.md](services.md) - サービス層設計
- [component-dependency.md](component-dependency.md) - 依存関係・データフロー
