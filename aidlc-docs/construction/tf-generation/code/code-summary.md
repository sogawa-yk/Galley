# Code Summary - Unit 2: Terraform Generation

## Generated Files

| File | Type | Purpose |
|---|---|---|
| `artifacts/skills/generate-terraform.md` | Skill | Terraform生成Skill本体（2フェーズ） |
| `artifacts/skills/tf-templates/provider-template.md` | Template | provider.tf参照パターン |
| `artifacts/skills/tf-templates/network-template.md` | Template | VCN/Subnet参照パターン（公式モジュール） |
| `artifacts/skills/tf-templates/compute-templates.md` | Template | OKE/CI/Compute/Functions参照パターン |
| `artifacts/skills/tf-templates/outputs-template.md` | Template | outputs.tf参照パターン |

## Test Files

| File | Type | Purpose |
|---|---|---|
| `artifacts/tests/test_tf_generation/expected_files_ecommerce.md` | Expected | Eコマース: 期待ファイル一覧+検証チェック |
| `artifacts/tests/test_tf_generation/expected_files_api.md` | Expected | APIサーバー: 期待ファイル一覧+検証チェック |

## Testing Procedure (Agent Separation - DC-5)

### テストエージェント
1. Unit 1テストで生成された `hearing/result.json` を入力として使用
2. generate-terraform.md Skillを実行
3. `generated/{project_name}/terraform/` に生成されたファイルを観測

### 評価エージェント
- [ ] 生成ファイルが expected_files_*.md の一覧と一致するか
- [ ] provider.tfにbackendブロックがないか
- [ ] 公式モジュールが適切に使われているか（VCN, OKE）
- [ ] 命名規則・タグ付けが一貫しているか
- [ ] outputs.tfに後続ユニットが必要な情報が含まれているか
- [ ] terraform validateが通るか（構文チェック）
