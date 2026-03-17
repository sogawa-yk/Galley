# Code Generation Plan - Unit 2: Terraform Generation

## Unit Context
- **Unit**: Terraform Generation
- **Requirements**: FR-3（Terraformコード自動生成）
- **Components**: C-2 generate-terraform.md (Skill)
- **Python Modules**: なし（Claude Codeの生成能力でTerraformコードを生成）
- **Dependencies**: Unit 1 (hearing/result.json)
- **Output**: `generated/{project-name}/terraform/`

## Code Location
- **Skills**: `artifacts/skills/`
- **Templates**: `artifacts/skills/tf-templates/`
- **Documentation**: `aidlc-docs/construction/tf-generation/code/`

## Generation Steps

### Step 1: Terraform Generation Skill作成
- [x] `artifacts/skills/generate-terraform.md` を作成
  - Phase 1: result.json読み込みとリソース特定
  - Phase 2: ファイル生成（provider.tf, variables.tf, network.tf, compute.tf, etc.）
  - 公式モジュール参照ルール
  - 命名規則・タグ付けルール
  - outputs.tf の生成ルール（後続ユニットが必要とする情報）

### Step 2: Terraform参照テンプレート作成
- [x] `artifacts/skills/tf-templates/` ディレクトリ作成
- [x] `artifacts/skills/tf-templates/provider-template.md` — provider.tfの参照パターン
- [x] `artifacts/skills/tf-templates/network-template.md` — VCN/Subnet/Gatewayの参照パターン（公式モジュール使用）
- [x] `artifacts/skills/tf-templates/compute-templates.md` — OKE/CI/Compute/Functionsの参照パターン
- [x] `artifacts/skills/tf-templates/outputs-template.md` — outputs.tfの参照パターン

### Step 3: テスト用期待出力作成
- [x] `artifacts/tests/test_tf_generation/` ディレクトリ作成
- [x] `artifacts/tests/test_tf_generation/expected_files_ecommerce.md` — Eコマースシナリオで生成されるべきファイル一覧と主要リソース
- [x] `artifacts/tests/test_tf_generation/expected_files_api.md` — APIサーバーシナリオで生成されるべきファイル一覧と主要リソース

### Step 4: ドキュメント生成
- [x] `aidlc-docs/construction/tf-generation/code/code-summary.md` を作成
