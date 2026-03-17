# Functional Design Plan - Unit 3: Infrastructure Deployment

## Plan Steps

- [x] ビジネスロジックモデル設計（business-logic-model.md）
- [x] ビジネスルール設計（business-rules.md）
- [x] ドメインエンティティ設計（domain-entities.md）
- [x] 設計の整合性検証

---

## Design Questions

## Question 1

Resource Manager Jobのポーリング間隔とタイムアウトはどの程度にしますか？

A) ポーリング30秒間隔、タイムアウト30分
B) ポーリング60秒間隔、タイムアウト60分
C) ポーリング30秒間隔、タイムアウト60分（大規模リソース対応）
D) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 2

Resource Manager Stackのコンパートメントはどのように決定しますか？

A) インスタンスプリンシパルのコンパートメントを自動取得して使用
B) 環境変数（OCI_COMPARTMENT_ID）から取得
C) ヒアリング時にユーザーに指定させる
D) Other (please describe after [Answer]: tag below)

[Answer]: A,B,Cの順に試していきましょう（最後はユーザーに尋ねる形で）
