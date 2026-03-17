# Code Generation Plan - Unit 1: Hearing

## Unit Context
- **Unit**: Hearing
- **Requirements**: FR-2（インタラクティブヒアリング）
- **Components**: C-1 hearing.md (Skill)
- **Python Modules**: なし（Claude Codeの自然言語能力で質問生成）
- **Dependencies**: なし（全ワークフローの起点）
- **Output**: `hearing/questions.md`, `hearing/result.json`

## Code Location
- **Workspace Root**: `/Users/sogawa/Documents/GitHub/aidlc-test`
- **Skills**: `artifacts/skills/`
- **Documentation**: `aidlc-docs/construction/hearing/code/`

## Generation Steps

### Step 1: Project Structure Setup
- [x] `artifacts/` ディレクトリ構成を作成
  - `artifacts/skills/`
  - `artifacts/workflows/`
  - `artifacts/src/`
  - `artifacts/tests/`
- [x] `artifacts/pyproject.toml` を作成（uv用、プロジェクト基本設定）
- [x] `artifacts/src/__init__.py` を作成

### Step 2: Hearing Skill作成
- [x] `artifacts/skills/hearing.md` を作成
  - Skill メタデータ（名前、説明、トリガー）
  - Phase 1: 要望解析の指示
  - Phase 2: 質問生成の指示（基本カテゴリテンプレート参照 + 動的追加）
  - Phase 3: 回答収集の指示（[Answer]:タグ読み取り）
  - Phase 4: 矛盾検出の指示（最大3ラウンド）
  - Phase 5: 構造化出力の指示（result.json生成）

### Step 3: 質問テンプレート作成
- [x] `artifacts/skills/hearing-templates/` ディレクトリ作成
- [x] `artifacts/skills/hearing-templates/base-questions.md` を作成
  - プロジェクト基本情報（必須）
  - アプリケーション種別（必須）
  - インフラ構成（必須）
  - データベース要件（条件付き）
  - ネットワーク構成（条件付き）
  - 追加サービス（条件付き）
- [x] `artifacts/skills/hearing-templates/result-schema.md` を作成
  - result.json の共通フィールド定義
  - 動的フィールドのガイドライン

### Step 4: テスト用サンプル作成
- [x] `artifacts/tests/test_hearing/` ディレクトリ作成
- [x] `artifacts/tests/test_hearing/sample_request_ecommerce.md` を作成（Eコマースデモ要望サンプル）
- [x] `artifacts/tests/test_hearing/expected_result_ecommerce.json` を作成（期待されるresult.json）
- [x] `artifacts/tests/test_hearing/sample_request_api.md` を作成（APIサーバー要望サンプル）
- [x] `artifacts/tests/test_hearing/expected_result_api.json` を作成（期待されるresult.json）

### Step 5: ドキュメント生成
- [x] `aidlc-docs/construction/hearing/code/code-summary.md` を作成
  - 生成されたファイル一覧
  - ファイルごとの役割説明
  - テスト方法の説明（エージェント分離テスト手順）

## Testing Strategy (DC-5: Agent Separation)

Unit 1のテストはSkillの品質評価が主目的のため、以下のエージェント分離を実施:

1. **開発エージェント（メイン）**: hearing.md と テンプレートを作成
2. **テストエージェント（別ワークツリー）**:
   - テスト用ワークスペースに hearing.md をコピー
   - サンプル要望（sample_request_*.md）を入力として Skill を実行
   - 生成された questions.md と result.json を観測
3. **評価エージェント（別エージェント）**:
   - テスト結果と期待値（expected_result_*.json）を比較
   - 質問の品質、矛盾検出の正確さ、result.json の構造を評価
   - フィードバックを開発エージェントに返す
