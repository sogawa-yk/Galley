# Unit of Work Plan

## Plan Steps

- [x] ユニット分割方針の決定
- [x] ユニット定義（unit-of-work.md）生成
- [x] ユニット依存関係（unit-of-work-dependency.md）生成
- [x] ユニット-要件マッピング（unit-of-work-story-map.md）生成
- [x] コード構成戦略のドキュメント化
- [x] ユニット境界と依存関係の検証

---

## Design Questions

### Unit Decomposition

## Question 1

ユニットの分割粒度はどのようにしますか？

A) ワークフローフェーズ単位 — 各Skill+対応Pythonモジュールを1ユニットとする（6ユニット: Hearing, TF Gen, Infra Deploy, App Gen, App Deploy, Verify + Orchestration）
B) レイヤー単位 — Python基盤層(oci_cli, oci_rm, deployer, e2e_runner, reporter)を1ユニット、Skill/Workflow層を1ユニットとする（2ユニット）
C) ハイブリッド — Python基盤を先に1ユニットで作り、その上にSkill/Workflow群を1ユニットで作る（2ユニット、レイヤー順に開発）
D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2

開発順序の優先度はどうしますか？

A) ボトムアップ — Python基盤モジュールから先に開発し、その上にSkillを構築
B) トップダウン — Workflowとスキルの骨組みから先に作り、Python実装を後から埋める
C) エンドツーエンド — 1つのフェーズ（例: Hearing）を縦断的に完成させてから次へ
D) Other (please describe after [Answer]: tag below)

[Answer]:　C
