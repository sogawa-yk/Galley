# Functional Design Plan - Unit 1: Hearing

## Plan Steps

- [x] ビジネスロジックモデル設計（business-logic-model.md）
- [x] ビジネスルール設計（business-rules.md）
- [x] ドメインエンティティ設計（domain-entities.md）
- [x] 設計の整合性検証

---

## Design Questions

## Question 1

ヒアリングで質問を生成する際、質問のカテゴリやテンプレートをあらかじめ定義しますか？それとも完全にClaude Codeの判断に委ねますか？

A) テンプレート型 — よくある質問パターン（インフラ構成、アプリ種別、規模など）をMarkdownテンプレートとして事前定義し、要望に応じて選択・カスタマイズ
B) 完全動的 — ユーザーの要望テキストのみを入力とし、Claude Codeが質問を一から生成
C) ハイブリッド — 基本カテゴリ（必須質問）は事前定義し、追加質問はClaude Codeが動的生成
D) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 2

ヒアリング結果（`hearing/result.json`）の構造はどの程度標準化しますか？

A) 厳密なスキーマ定義 — JSONスキーマを事前定義し、後続ユニットはそのスキーマに依存する
B) 柔軟な構造 — キーとなるフィールド（project_name, app_type, infra_resources等）のみ共通化し、詳細は動的
C) 自由形式 — Claude Codeが要望に応じて自由にJSONを構成する
D) Other (please describe after [Answer]: tag below)

[Answer]:　B

## Question 3

矛盾検出と追加質問のサイクルは最大何回まで許容しますか？

A) 1回（初回質問+1回の追加質問で打ち切り）
B) 2回まで（最大3ラウンドの質問）
C) 矛盾がなくなるまで無制限
D) Other (please describe after [Answer]: tag below)

[Answer]:　B

## Question 4

ヒアリングの質問ファイルはAI-DLCと同じMarkdown形式（選択肢+[Answer]:タグ）にしますか？

A) はい、AI-DLCと完全に同じ形式を採用する
B) 形式は似せるが、JSON出力用のメタデータ（フィールド名など）を追加する
C) Other (please describe after [Answer]: tag below)

[Answer]:　A
