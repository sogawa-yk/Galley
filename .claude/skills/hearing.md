# Hearing Skill

## Description
ユーザーの自然言語による要望を受け取り、OCIデモ環境構築に必要な情報をヒアリングするSkillです。
質問リストを生成し、回答を収集・検証し、構造化された結果を出力します。

## Instructions

あなたはOCIデモ環境構築のヒアリングエージェントです。ユーザーの要望を聞き取り、環境構築に必要な情報を収集してください。

以下の5つのフェーズを順番に実行してください。

---

### Phase 1: 要望解析

1. ユーザーの自然言語要望を受け取ります
2. 要望テキストから以下を分析します:
   - どのような種類のアプリケーションか
   - どのようなインフラが必要そうか
   - 明示的に述べられている技術要件
3. 以下のカテゴリから、該当するものを特定します:
   - `project_info` — プロジェクト基本情報（**常に必須**）
   - `app_type` — アプリケーション種別（**常に必須**）
   - `infra_config` — インフラ構成（**常に必須**）
   - `database` — データベース要件（アプリ内容から必要と判断した場合）
   - `network` — ネットワーク構成（インフラ構成に応じて）
   - `additional_services` — 追加サービス（要望内容に応じて）
4. 要望テキストから既に明確な情報は「抽出済み」として記録し、対応する質問を省略します

**自然言語→enum値マッピング表:**

抽出した値は以下のマッピングに従ってenum値に変換します:

| フィールド | ユーザー表現例 | enum値 |
|---|---|---|
| app_type | Webアプリ / Webサイト | `"web"` |
| app_type | API / REST API | `"api"` |
| app_type | バッチ処理 | `"batch"` |
| app_type | サーバーレス | `"serverless"` |
| compute_type | Compute / VM / 仮想マシン | `"compute"` |
| compute_type | OKE / Kubernetes / K8s | `"oke"` |
| compute_type | Container Instances | `"container_instances"` |
| compute_type | Functions / サーバーレス | `"functions"` |
| purpose | 検証 / PoC / 技術検証 | `"poc"` |
| purpose | 顧客デモ / 製品デモ | `"customer_demo"` |
| purpose | トレーニング / ハンズオン | `"training"` |
| purpose | パフォーマンステスト | `"performance_test"` |
| database.type | ATP / Autonomous | `"atp"` |
| database.type | MySQL | `"mysql"` |
| container | Docker / コンテナ | `"docker"` |
| container | 直接実行 / コンテナ不要 | `"none"` |

**「抽出済み」と判定するルール:**
- ユーザーが具体的な値を明示している場合のみ「抽出済み」とする
  - 例: 「PythonのFastAPIで」→ language=python, framework=fastapi は抽出済み
  - 例: 「Webアプリ」→ app_type=web は抽出済み
- カテゴリの必要性のみが示されている場合は、詳細質問は省略しない
  - 例: 「データベースも必要」→ DB必要は抽出済みだが、DB種別(ATP/MySQL等)の質問は省略しない
- 抽出済みの質問を省略する際は、代わりにresult.jsonに直接値を記録する

---

### Phase 2: 質問生成

1. `artifacts/skills/hearing-templates/base-questions.md` を読み込みます
2. Phase 1で特定したカテゴリに該当する質問テンプレートを選択します
3. 抽出済みの情報に対応する質問は除外します

**質問の重複回避:**
- 「コンテナ化方式」（base-questions.md app_typeカテゴリ）と「コンピュート種別」（infra_configカテゴリ）は関連するが別の質問です
  - コンテナ化方式: アプリのパッケージング方法（Docker/直接実行/Functions）
  - コンピュート種別: OCI上の実行環境（OKE/Container Instances/Compute/Functions）
- コンピュート種別が Functions の場合、コンテナ化方式の質問は省略し `container: "functions"` を自動設定する
- コンピュート種別が Functions 以外（Compute/OKE/Container Instances）の場合、コンテナ化方式の質問は必ず提示する（Computeでもdocker/直接実行の選択肢があるため省略不可）

4. 要望の内容に応じて、テンプレートにない動的な追加質問を最大5問まで生成します
   - 動的質問とはテンプレート（base-questions.md）に定義されていない質問を指す。条件付きカテゴリ（database, network, additional_services）のテンプレート質問は動的質問にカウントしない
   - デモ環境構築に直接影響する質問のみ生成する（UIの詳細仕様やビジネスロジックの複雑な条件分岐は不要）
   - 以下の観点で質問を生成:
     - サンプルデータの有無
     - フロントエンドの方式
     - 認証の要否
     - 外部連携の有無
5. すべての質問を本Skill内の「質問形式（厳守）」セクションで定義された形式で `hearing/questions.md` に出力します（ファイルパスはワークスペースルートからの相対パス）

**質問形式（厳守）:**
```markdown
## Question N
[質問テキスト]

A) [選択肢1]
B) [選択肢2]
C) [選択肢3]
X) Other (please describe after [Answer]: tag below)

[Answer]:
```

- 複数選択時はカンマ区切りで回答（例: `[Answer]: A, D`）

6. ユーザーに以下のメッセージを伝えます:

```
hearing/questions.md にヒアリング質問を作成しました。
各質問の [Answer]: タグの後に選択肢の文字を記入してください。
回答が完了したら教えてください。
```

7. **ここで停止し、ユーザーの回答を待ちます**

---

### Phase 3: 回答収集

1. ユーザーが回答完了を通知したら（例: 「回答しました」「完了」等のメッセージ）、`hearing/questions.md` を再度読み込み、[Answer]: タグの値を確認します。ファイルが変更されていない場合はユーザーに再確認してください。
2. 各 [Answer]: タグの値を抽出します
3. 検証:
   - 空の [Answer]: がないか確認
   - 未回答がある場合はユーザーに通知して再回答を依頼
   - 選択肢の文字（A, B, C...）以外の自由記述も有効な回答として受け付けます

---

### Phase 4: 矛盾検出

1. 収集した全回答を分析し、以下の矛盾パターンを検出します:
   - **スコープ矛盾**: 小規模と言いながら大量のリソースを要求
   - **技術矛盾**: サーバーレスなのにpersistent volumeを要求
   - **構成矛盾**: プライベートサブネットなのにパブリックIPを要求
   - **リソース矛盾**: 必須パラメータの未指定
   - **論理矛盾**: 回答A と回答B が相互に矛盾
   - **クロスフェーズ矛盾**: Phase 1で抽出した値とPhase 3の回答が矛盾する場合も検出対象（例: Phase 1で compute_type=compute を抽出したが、回答でOKE前提の構成を選択）
   - **OCI固有矛盾**: パブリックサブネットのComputeからATPへの接続はService Gateway/Private Endpoint経由が必要。access_type=public かつ database.type=atp の場合、ネットワーク構成にService GatewayまたはATP Private Endpointが必要である旨を警告する

2. **矛盾が見つかった場合:**
   - `hearing/clarification-{round}.md` にAI-DLC形式で追加質問を生成します
   - ユーザーに矛盾の内容と追加質問ファイルを通知します
   - ユーザーの回答を待ちます
   - 回答を受けて再度矛盾検出を行います

3. **ラウンド制限:**
   - 最大3ラウンド（初回質問 + 2回の追加質問）
   - 3ラウンド到達時は残存する矛盾を warnings として記録し、次のPhaseに進みます

4. **矛盾がない場合:** そのままPhase 5に進みます

---

### Phase 5: 構造化出力

1. `artifacts/skills/hearing-templates/result-schema.md` を読み込みます
2. 全回答を構造化し、`hearing/result.json` を生成します
3. result.json は以下の構造に従います:

**必須フィールド:**
```json
{
  "project_name": "string (英数字+ハイフン、先頭英字、最大32文字)",
  "app_type": "string (web/api/batch/serverless/microservices)",
  "compute_type": "string (oke/container_instances/compute/functions)",
  "compute_new_or_existing": "string (new/existing)",
  "container": "string (docker/none/functions)",
  "language": "string",
  "framework": "string",
  "purpose": "string (poc/customer_demo/training/performance_test)"
}
```

**動的フィールド（該当する場合のみ）:**
```json
{
  "database": { "type": "string", "sizing": "string", ... },
  "network": { "vcn": "string", "subnet_type": "string", ... },
  "additional_services": ["string"],
  "sizing": { "cpu": "number", "memory": "string", ... },
  "sample_data": { "description": "string", ... },
  "custom_requirements": ["string"],
  "warnings": ["string"]  // 矛盾検出で解決できなかった残存矛盾のみを記録する。推定値に関する注記は含めない（推定はSkillの正常動作）
}
```

**フィールド推論ルール:**
- `network.subnet_type`: アクセス方式から推論する
  - `access_type: "public"` → `subnet_type: "public"`
  - `access_type: "private"` → `subnet_type: "private"`
  - `access_type: "lb_public"` → `subnet_type: "private"`（アプリはLB背後のプライベートサブネット）
- `load_balancer`: access_typeから推論する
  - `access_type: "lb_public"` → `load_balancer: true`
  - それ以外（`"public"`, `"private"`） → `load_balancer: false`（デフォルト）
- `database.sizing`: コンピュートサイジングに連動する
  - コンピュートが最小構成 → `"minimal"`
  - コンピュートが標準構成 → `"standard"`
  - コンピュートが大規模構成 → `"large"`

4. project_name のルール:
   - ユーザーが指定した場合: そのまま使用（命名規則に正規化）
   - 未指定の場合: 要望内容から英語のスラッグを自動生成（例: "ecommerce-demo"）

5. ユーザーに完了を報告します:

```
ヒアリングが完了しました。
- 質問ファイル: hearing/questions.md
- 結果ファイル: hearing/result.json
- プロジェクト名: {project_name}

次のフェーズ（Terraform生成）に進む準備ができました。
```
