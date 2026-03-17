# Application Design Plan

## Plan Steps

- [x] コンポーネント設計（components.md）
- [x] コンポーネントメソッド設計（component-methods.md）
- [x] サービス層設計（services.md）
- [x] コンポーネント依存関係設計（component-dependency.md）
- [x] 統合設計ドキュメント（application-design.md）
- [x] 設計の整合性検証

---

## Design Questions

以下の質問に回答してください。各質問の `[Answer]:` タグの後に選択肢の文字を記入してください。

### Skill/Workflow構成

## Question 1

Workflowのエントリーポイントはどのような粒度にしますか？

A) 単一Workflow（`/build-demo-env`）で全フェーズを統括する
B) フェーズごとに独立したWorkflow（`/hearing`, `/deploy-infra`, `/deploy-app`, `/verify`）を作り、メインWorkflowから呼び出す
C) Other (please describe after [Answer]: tag below)

[Answer]:　B

## Question 2

ヒアリングフェーズで生成する質問の保存先はどこにしますか？

A) ワークスペース内のMarkdownファイル（例: `hearing/questions.md`）— AI-DLC方式
B) 標準出力に直接表示してインタラクティブに回答を受ける
C) JSON形式のファイルとしてプログラム的に管理する
D) Other (please describe after [Answer]: tag below)

[Answer]:　A

## Question 3

生成したTerraformコード、アプリケーションコードの出力先ディレクトリ構成はどうしますか？

A) プロジェクト名ベースのディレクトリ（例: `generated/{project-name}/terraform/`, `generated/{project-name}/app/`）
B) タイムスタンプベースのディレクトリ（例: `generated/2026-03-15-demo/terraform/`）
C) OCI上のリモートディレクトリにのみ生成する（ローカルには保持しない）
D) Other (please describe after [Answer]: tag below)

[Answer]:　A

### OCI操作

## Question 4

OCI Resource Manager Stackへのアップロード方法はどれが適切ですか？

A) Terraformコードをzipに圧縮してOCI CLIでStack作成（`oci resource-manager stack create`）
B) Object Storageに一旦アップロードし、そのURLからStack作成
C) Other (please describe after [Answer]: tag below)

[Answer]:　A

## Question 5

デプロイ先のOKEクラスターやContainer Instancesは、Terraformで同時に作成しますか？それとも既存のものを使いますか？

A) Terraformで新規作成する（デモ環境ごとに独立したクラスター）
B) 既存の共有クラスター/インスタンスにデプロイする
C) 要件に応じて選択する（ヒアリングで確認）
D) Other (please describe after [Answer]: tag below)

[Answer]:　C

### メタ開発戦略

## Question 6

開発中のSkill/Workflowファイルの配置場所について、開発用と本番用をどう分離しますか？

A) 別リポジトリ（開発用リポジトリで開発し、完成後に本番用リポジトリへコピー）
B) 同一リポジトリ内で別ディレクトリ（例: `dev-skills/` で開発、完成後 `.claude/skills/` へコピー）
C) 同一リポジトリの `.claude/` に直接配置（開発と本番を分離しない）
D) Other (please describe after [Answer]: tag below)

[Answer]:　開発した成果物は、artifactsというディレクトリを作成してそこに配置しましょう

## Question 7

Pythonコアモジュールのパッケージ管理はどうしますか？

A) pip + requirements.txt
B) Poetry（pyproject.toml）
C) uv（高速パッケージマネージャー）
D) Other (please describe after [Answer]: tag below)

[Answer]:　C
