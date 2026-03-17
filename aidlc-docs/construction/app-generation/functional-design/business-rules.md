# Business Rules - Unit 4: App Generation

## BR-1: コード生成ルール

### BR-1.1: 完全新規生成
- テンプレートやスキャフォールドは使用しない
- Claude Codeが要件に応じて毎回新規にコードを生成する
- ヒアリング結果に含まれるビジネス要件を反映する

### BR-1.2: 言語/フレームワーク対応
| language | framework | 生成パターン |
|---|---|---|
| python | fastapi | FastAPI + uvicorn |
| python | flask | Flask |
| java | spring-boot | Spring Boot + Maven |
| nodejs | express | Express.js |
| nodejs | nestjs | NestJS |
| go | gin | Gin |
| go | echo | Echo |

### BR-1.3: デモ品質
- 本番品質ではなくデモ/検証用途に適したコード
- 主要機能が動作することを優先
- エラーハンドリングは基本的なレベル

## BR-2: プロジェクト構成ルール

### BR-2.1: 出力ディレクトリ
- `generated/{project_name}/app/` に全ファイルを出力
- 言語標準のプロジェクト構成に従う

### BR-2.2: DB接続
- DB使用時: 環境変数で接続情報を受け取る設計
- 環境変数名: `DB_CONNECTION_STRING` (stack_outputs.jsonのdb_connection_stringに対応)
- DB未使用時: インメモリデータストアやモックデータを使用

### BR-2.3: ポート設定
- デフォルトポート: 8080
- 環境変数 `PORT` で上書き可能

## BR-3: テストルール

### BR-3.1: テストカバレッジ
- 全APIエンドポイントの正常系テスト
- 主要なエラーケース（不正入力、404等）
- DB操作のCRUDテスト（DB使用時）

### BR-3.2: テスト実行
- 生成直後にテストを実行する
- 言語標準のテストランナーを使用

### BR-3.3: 自己修正ループ
- テスト失敗時: Claude Codeがエラー内容を分析してコードを修正
- 最大3回の修正ループ
- 修正後は全テストを再実行

## BR-4: Dockerfileルール

### BR-4.1: マルチステージビルド
- Stage 1 (builder): 依存関係インストール + ビルド
- Stage 2 (runtime): 最小イメージでアプリ実行

### BR-4.2: ベースイメージ
| language | builder | runtime |
|---|---|---|
| python | python:3.12-slim | python:3.12-slim |
| java | eclipse-temurin:21-jdk | eclipse-temurin:21-jre |
| nodejs | node:20-slim | node:20-slim |
| go | golang:1.22 | gcr.io/distroless/static |

### BR-4.3: ヘルスチェック
- Dockerfileに `HEALTHCHECK` を含める
- ヘルスチェックエンドポイント: `/health`
- アプリコードに `/health` エンドポイントを必ず実装する

## BR-5: data-testid属性
- HTMLを含むWebアプリの場合、主要なUI要素に `data-testid` 属性を付与
- E2Eテスト（Unit 6）での要素特定に使用
