# Unit of Work Definitions

## Decomposition Strategy
- **Granularity**: ワークフローフェーズ単位（各Skill+対応Pythonモジュールで1ユニット）
- **Development Order**: エンドツーエンド（1ユニットを縦断的に完成させてから次へ）
- **Total Units**: 7

## Development Order & Unit Definitions

### Unit 1: Hearing
- **Scope**: ヒアリングフェーズ全体
- **Components**: C-1 hearing.md (Skill)
- **Python Modules**: なし（Claude Codeの自然言語能力で質問生成・回答分析）
- **Output**: `hearing/questions.md`, `hearing/result.json`
- **Rationale**: 全ワークフローの起点。他ユニットへの入力データを生成するため最初に開発。Python不要で最も独立性が高い。

### Unit 2: Terraform Generation
- **Scope**: Terraformコード自動生成
- **Components**: C-2 generate-terraform.md (Skill)
- **Python Modules**: なし（Claude Codeの生成能力でTerraformコードを生成）
- **Output**: `generated/{project-name}/terraform/`
- **Rationale**: ヒアリング結果を入力とする最初の生成フェーズ。Python不要。

### Unit 3: Infrastructure Deployment
- **Scope**: OCI Resource Managerによるインフラ構築
- **Components**: C-3 deploy-infra.md (Skill), C-8 oci_rm.py, C-9 oci_cli.py
- **Python Modules**: `oci_rm.py`, `oci_cli.py`（新規作成）
- **Output**: `generated/{project-name}/stack_outputs.json`
- **Rationale**: 初めてPythonモジュールを必要とするユニット。oci_cli.pyは後続ユニットでも共有される基盤モジュール。

### Unit 4: App Generation
- **Scope**: アプリケーションコード自動生成+単体テスト+結合テスト
- **Components**: C-4 generate-app.md (Skill)
- **Python Modules**: なし（Claude Codeの生成能力でアプリコード・テストを生成・実行）
- **Output**: `generated/{project-name}/app/`
- **Rationale**: Unit 3と並行実行される前提で設計。Python不要。

### Unit 5: App Deployment
- **Scope**: アプリケーションビルド・デプロイ
- **Components**: C-5 deploy-app.md (Skill), C-10 deployer.py
- **Python Modules**: `deployer.py`（新規作成）、`oci_cli.py`（Unit 3で作成済み、再利用）
- **Output**: `generated/{project-name}/endpoints.json`
- **Rationale**: Unit 3（インフラ）とUnit 4（アプリ）の両方に依存。

### Unit 6: Verification
- **Scope**: E2Eテスト・動作確認
- **Components**: C-6 verify.md (Skill), C-11 e2e_runner.py
- **Python Modules**: `e2e_runner.py`（新規作成）
- **Output**: `generated/{project-name}/test_results.json`
- **Rationale**: デプロイ完了後にのみ実行可能。

### Unit 7: Orchestration
- **Scope**: メインWorkflow+レポーティング
- **Components**: C-7 build-demo-env.md (Workflow), C-12 reporter.py
- **Python Modules**: `reporter.py`（新規作成）
- **Output**: `generated/{project-name}/summary.md`
- **Rationale**: 全ユニットを統括するため最後に開発。全Skillの動作を確認した上でWorkflowを構成。

## Code Organization Strategy (Greenfield)

```
artifacts/
  skills/
    hearing.md              # Unit 1
    generate-terraform.md   # Unit 2
    deploy-infra.md         # Unit 3
    generate-app.md         # Unit 4
    deploy-app.md           # Unit 5
    verify.md               # Unit 6
  workflows/
    build-demo-env.md       # Unit 7
  src/
    __init__.py
    oci_cli.py              # Unit 3 (shared)
    oci_rm.py               # Unit 3
    deployer.py             # Unit 5
    e2e_runner.py           # Unit 6
    reporter.py             # Unit 7
  tests/
    test_oci_cli.py         # Unit 3
    test_oci_rm.py          # Unit 3
    test_deployer.py        # Unit 5
    test_e2e_runner.py      # Unit 6
    test_reporter.py        # Unit 7
  pyproject.toml
```

## Shared Module Strategy

`oci_cli.py`はUnit 3で初めて作成され、Unit 5でも再利用される。
- Unit 3開発時: `oci_cli.py` + `oci_rm.py` をセットで作成・テスト
- Unit 5開発時: `oci_cli.py` は既存を利用し、必要に応じて拡張
