# Domain Entities - Unit 1: Hearing

## Entity: HearingSession

セッション全体を管理するエンティティ。

```
HearingSession
  - project_name: str           # プロジェクト名
  - user_request: str           # ユーザーの元の要望テキスト
  - detected_categories: list   # 検出されたカテゴリ
  - extracted_info: dict        # 要望から抽出済みの情報
  - current_round: int          # 現在のラウンド (1-3)
  - status: str                 # pending/collecting/validating/complete
  - questions_file: str         # 質問ファイルパス
  - clarification_files: list   # 追加質問ファイルパスのリスト
  - result_file: str            # 結果ファイルパス
```

## Entity: QuestionCategory

質問カテゴリの定義。

```
QuestionCategory
  - id: str                     # カテゴリID (project_info, app_type, etc.)
  - name: str                   # カテゴリ表示名
  - required: bool              # 必須カテゴリかどうか
  - questions: list[Question]   # カテゴリに属する質問リスト
  - condition: str | None       # 条件付きカテゴリの条件式
```

## Entity: Question

個別の質問。

```
Question
  - id: str                     # 質問ID (q1, q2, etc.)
  - category_id: str            # 所属カテゴリID
  - text: str                   # 質問テキスト
  - options: list[Option]       # 選択肢リスト
  - answer: str | None          # ユーザーの回答 (A, B, C... or free text)
  - result_field: str           # result.json のマッピング先フィールド名
  - is_dynamic: bool            # 動的生成された質問かどうか
```

## Entity: Option

質問の選択肢。

```
Option
  - letter: str                 # A, B, C, D, E, X
  - text: str                   # 選択肢テキスト
  - is_other: bool              # Other選択肢かどうか
```

## Entity: ContradictionCheck

矛盾検出の結果。

```
ContradictionCheck
  - round: int                  # 検出ラウンド
  - contradictions: list[Contradiction]
  - resolved: bool              # すべて解決済みか
```

## Entity: Contradiction

個別の矛盾。

```
Contradiction
  - type: str                   # scope/technical/config/resource/logical
  - question_ids: list[str]     # 関連する質問ID
  - description: str            # 矛盾の説明
  - clarification_question: Question  # 解決用の追加質問
  - resolved: bool              # 解決済みか
```

## Entity: HearingResult

最終出力（result.json の構造）。

```
HearingResult
  # 共通フィールド（必須）
  - project_name: str
  - app_type: str
  - compute_type: str           # oke/container_instances/compute/functions
  - compute_new_or_existing: str # new/existing
  - language: str
  - framework: str

  # 動的フィールド（任意）
  - database: dict | None
  - network: dict | None
  - additional_services: list | None
  - sizing: dict | None
  - sample_data: dict | None
  - custom_requirements: list | None
  - warnings: list[str]         # 残存矛盾の警告リスト
```

## Entity Relationships

```
HearingSession 1---* QuestionCategory
QuestionCategory 1---* Question
Question 1---* Option
HearingSession 1---* ContradictionCheck
ContradictionCheck 1---* Contradiction
Contradiction *---1 Question (clarification)
HearingSession 1---1 HearingResult
```
