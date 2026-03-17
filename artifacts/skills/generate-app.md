# Generate Application Skill

## Description
ヒアリング結果に基づき、デモ用・検証用のアプリケーションコードを自動生成し、テストまで実行するSkillです。
アプリケーションは事前テンプレートを使用せず、要件に応じてClaude Codeが毎回新規に生成します。

## Instructions

あなたはアプリケーション開発エージェントです。ヒアリング結果を元に、デモ用アプリケーションのコード生成からテスト実行まで行ってください。

以下の4つのフェーズを順番に実行してください。

---

### Phase 1: 要件解析

1. `hearing/result.json` を読み込みます
2. 以下のフィールドを確認します:
   - `app_type`: アプリケーション種別（web/api/batch/serverless/microservices）
   - `language`: プログラミング言語
   - `framework`: フレームワーク
   - `compute_type`: デプロイ先 → Dockerfile方式の決定
   - `database`: DB有無と種別 → DB接続コード生成の要否
   - `sample_data`: サンプルデータ要件
   - `custom_requirements`: カスタム要件
3. アプリの機能スコープを決定します（ヒアリング時のユーザー要望を反映）
4. スコープ決定結果をコメントとしてユーザーに報告してください（ファイル出力不要）

---

### Phase 2: アプリコード生成

`generated/{project_name}/app/` ディレクトリを作成し、アプリケーションコードを生成してください。

**生成ガイドライン:**

1. **言語/フレームワーク標準のプロジェクト構成**に従ってください
2. **必ず `/health` エンドポイントを実装**してください（E2Eテスト・ヘルスチェック用）
   ```json
   GET /health → {"status": "ok"}
   ```
3. **DB使用時**: 環境変数 `DB_CONNECTION_STRING` で接続情報を受け取る設計にしてください
4. **ポート**: デフォルト `8080`、環境変数 `PORT` で上書き可能
5. **デモ品質**: 主要機能が動作することを優先、過度なエラーハンドリングは不要
6. **Webアプリの場合**: 主要UI要素に `data-testid` 属性を付与
7. **サンプルデータ**: `sample_data` が指定されている場合、シードデータ/初期データを含める
8. **シードデータ実行**: `sample_data.seed_required=true` の場合、アプリ起動時にべき等なシードを実行（存在チェック後に挿入）
9. **シード認証情報の出力**: 認証機能がある場合、シードデータのログイン情報を `generated/{project_name}/app/seed-credentials.json` に出力してください:
   ```json
   {"username": "admin", "password": "password123"}
   ```
   verifyスキルがこのファイルを読み取ってE2Eテストの認証に使用します。

**データベースローカル開発戦略:**

| database.type | Local開発用DB | ORM |
|---|---|---|
| atp | SQLite (ローカル) / Oracle (本番) | SQLAlchemy |
| mysql | SQLite (ローカル) / MySQL (本番) | SQLAlchemy / Sequelize |

> ローカルテスト時はSQLiteを使用し、`DB_CONNECTION_STRING`が未設定の場合はSQLiteにフォールバックする設計にしてください

**言語/フレームワーク別ガイダンス:**

| 言語/FW | プロジェクト構成 | ORM | テストFW | 依存管理 |
|---|---|---|---|---|
| Python/FastAPI | routers/, models.py, schemas.py, database.py | SQLAlchemy | pytest | requirements.txt |
| Python/Flask | routes/, models.py | SQLAlchemy | pytest | requirements.txt |
| Node.js/Express | routes/, models/, middleware/ | Sequelize/Prisma | Jest | package.json |

**認証パターン（custom_requirementsに認証要件がある場合）:**
- Web app (app_type=web): セッションベース認証（express-session/Flask-Login）
- API (app_type=api): JWT認証（jsonwebtoken/PyJWT）
- エンドポイント: POST /auth/login (ログイン), POST /auth/logout (ログアウト), GET /auth/register (登録画面 - web only)

**テンプレートエンジン（app_type=webの場合）:**
- Node.js/Express: EJSをデフォルト使用、views/ディレクトリにテンプレート配置
- Python/Flask: Jinja2（デフォルト）、templates/ディレクトリ
- Python/FastAPI: Jinja2Templates、templates/ディレクトリ

**アプリ種別別の生成内容:**

| app_type | 生成内容 |
|---|---|
| web | フロントエンド + バックエンドAPI |
| api | REST APIエンドポイント群 |
| batch | バッチ処理スクリプト + エントリーポイント |
| serverless | OCI Functions用のfunc.py/func.js + func.yaml |
| microservices | 複数サービス（各サービスにDockerfile） |

**app_type と compute_type の組み合わせ:**
- `app_type: api` + `compute_type: functions` → Flask/FastAPI APIをOCI Functions handlerでラップ。`func.py`でfdkを使用してFlaskアプリをハンドラーとして登録。
- `app_type: serverless` → 純粋なOCI Functions（Webフレームワーク不使用）

---

### Phase 3: テスト生成・実行（自己修正ループ）

**最大修正ループ: 3回**

1. **単体テスト**を生成してください
   - ビジネスロジックのテスト
   - データモデルのテスト（DB使用時）
   - 言語標準のテストフレームワーク使用
   - テスト用DBはインメモリSQLiteを使用し、テストごとにリセットする

2. **結合テスト**を生成してください
   - 全APIエンドポイントの正常系テスト
   - 主要なエラーケース（不正入力、404等）
   - テストクライアントを使用（HTTPリクエストではなくアプリ内部テスト）

3. **テストを実行**してください
   - 依存関係をインストール
   - テストランナーを実行

4. **テスト失敗時の自己修正ループ:**
   - エラー内容を分析
   - アプリケーションコードまたはテストコードを修正
   - 全テストを再実行
   - 最大3回の修正ループ
   - 修正不能な場合: 失敗テストの詳細をユーザーに報告（ワークフローは継続）

5. テスト結果をユーザーに報告:
   ```
   テスト結果:
   - 単体テスト: X passed / Y total
   - 結合テスト: X passed / Y total
   ```

---

### Phase 4: ビルド設定生成

1. **Dockerfile** を `generated/{project_name}/app/Dockerfile` に生成（**`compute_type: functions` の場合はスキップ** — `fn deploy` が `func.yaml` を使用してビルドするため、別途Dockerfileは不要）
   - マルチステージビルド（builder + runtime）
   - `HEALTHCHECK` 命令を含める（`/health` エンドポイント）
   - `EXPOSE 8080`
   - Dockerfileは `generated/{project_name}/app/Dockerfile` に配置。CMD のモジュールパスはDockerfile内の`WORKDIR`とソースコピー先に合わせてください。例: `WORKDIR /app` + `COPY . .` → `CMD ["uvicorn", "main:app"]`（`app.main`ではなく`main`）
   - ランタイムステージでは非rootユーザーで実行してください（`RUN adduser --disabled-password appuser && USER appuser`）

2. **`.dockerignore`** を生成してください（`.venv/`, `__pycache__/`, `*.pyc`, `tests/`, `.pytest_cache/`, `node_modules/`, `*.test.*` を除外）

3. **OCI Functions の場合**: `func.yaml` を生成

4. **build.sh** をオプションで生成（ローカルビルド・テスト用）

---

### 完了報告

```
アプリケーションコードを生成しました。
- 出力先: generated/{project_name}/app/
- 言語/FW: {language}/{framework}
- テスト結果: 単体テスト {X}/{Y} passed, 結合テスト {X}/{Y} passed
- Dockerfile: 生成済み
- ヘルスチェック: GET /health

次のフェーズ（アプリデプロイ）に進む準備ができました。
```

---

### 注意事項

- このSkillはインフラ構築（Unit 3: deploy-infra）と**並行実行**されます
- インフラの完了を待つ必要はありません
- 生成したコードとテストはローカル環境で完結します
- デプロイは次のUnit（deploy-app）が担当します
