# Code Summary - Unit 1: Hearing

## Generated Files

| File | Type | Purpose |
|---|---|---|
| `artifacts/skills/hearing.md` | Skill | ヒアリングSkill本体（5フェーズの実行指示） |
| `artifacts/skills/hearing-templates/base-questions.md` | Template | 基本カテゴリ質問テンプレート（6カテゴリ、12質問） |
| `artifacts/skills/hearing-templates/result-schema.md` | Schema | result.json の構造定義 |
| `artifacts/pyproject.toml` | Config | uvパッケージ管理設定 |
| `artifacts/src/__init__.py` | Python | パッケージ初期化 |

## Test Files

| File | Type | Purpose |
|---|---|---|
| `artifacts/tests/test_hearing/sample_request_ecommerce.md` | Test Input | Eコマースデモ要望サンプル |
| `artifacts/tests/test_hearing/expected_result_ecommerce.json` | Expected | 期待されるresult.json |
| `artifacts/tests/test_hearing/sample_request_api.md` | Test Input | APIサーバー要望サンプル |
| `artifacts/tests/test_hearing/expected_result_api.json` | Expected | 期待されるresult.json |

## Testing Procedure (Agent Separation - DC-5)

### 1. 開発エージェント（本エージェント）
- hearing.md、テンプレート、テストサンプルを作成済み

### 2. テストエージェント（別ワークツリー）
テスト手順:
1. テスト用ワークスペースを作成
2. `artifacts/skills/hearing.md` を `.claude/skills/hearing.md` にコピー
3. `artifacts/skills/hearing-templates/` を同じ相対パスにコピー
4. サンプル要望（`sample_request_ecommerce.md` の要望テキスト）を入力として hearing Skill を実行
5. 生成された `hearing/questions.md` を確認
6. 質問に回答
7. 生成された `hearing/result.json` を保存

### 3. 評価エージェント（別エージェント）
評価項目:
- [ ] 質問の網羅性: 必要な情報が全てカバーされているか
- [ ] 質問の品質: 選択肢が適切か、不要な質問がないか
- [ ] 矛盾検出: 矛盾がある回答を与えた場合に検出できるか
- [ ] result.json の構造: スキーマに準拠しているか
- [ ] result.json の内容: expected_result_*.json と主要フィールドが一致するか
- [ ] エッジケース: 曖昧な要望、最小限の要望、過剰な要望への対応

## Notes
- Unit 1 は Python モジュールを含まない（Skill + テンプレートのみ）
- 質問生成と矛盾検出はClaude Codeの自然言語能力に依存
- テストは自動化テストではなくエージェント分離テストで実施
