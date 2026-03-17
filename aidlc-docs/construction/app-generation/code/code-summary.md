# Code Summary - Unit 4: App Generation

## Generated Files

| File | Type | Purpose |
|---|---|---|
| `artifacts/skills/generate-app.md` | Skill | アプリコード生成Skill（4フェーズ: 要件解析→コード生成→テスト実行→ビルド設定） |

## Functional Design

| File | Purpose |
|---|---|
| `aidlc-docs/construction/app-generation/functional-design/business-logic-model.md` | 4フェーズフロー、テスト自己修正ループ |
| `aidlc-docs/construction/app-generation/functional-design/business-rules.md` | コード生成、テスト、Dockerfile、data-testidルール |

## Key Design Decisions

- **テンプレート不使用**: Claude Codeが毎回新規にコード生成（デモ用途に最適）
- **自己修正ループ**: テスト失敗時に最大3回コード修正→再テスト
- **並行実行対応**: Unit 3（Infra Deploy）と並行実行、インフラ完了を待たない
- **ヘルスチェック必須**: `/health` エンドポイントを全アプリに実装（Unit 6のE2Eテストで使用）
- **DB接続は環境変数**: `DB_CONNECTION_STRING` でstack_outputs.jsonの値を受け取る

## Testing (DC-5)

### テストエージェント
1. サンプルresult.json（ecommerce）を入力として generate-app.md を実行
2. 生成されたコードとテスト結果を観測

### 評価エージェント
- [ ] 要件に応じた適切なコードが生成されているか
- [ ] /health エンドポイントが実装されているか
- [ ] 単体テスト・結合テストが通過しているか
- [ ] Dockerfileが適切に生成されているか
- [ ] DB接続コードが環境変数ベースになっているか
