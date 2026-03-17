# Business Logic Model - Unit 4: App Generation

## Overview

App Generation Skillは4段階のフローで動作する：
1. **要件解析**: hearing/result.jsonからアプリ要件を解析
2. **アプリコード生成**: 要件に応じたアプリケーションコードをClaude Codeが生成
3. **テスト生成・実行**: 単体テスト・結合テストを生成し実行
4. **ビルド設定生成**: Dockerfile、ビルドスクリプトを生成

## フロー詳細

```
hearing/result.json
      |
      v
[Phase 1: 要件解析]
      | app_type, language, framework 解析
      | デプロイ先（compute_type）確認
      v
[Phase 2: アプリコード生成]
      | アプリケーションコード（Claude Code生成）
      | -> generated/{project-name}/app/src/
      v
[Phase 3: テスト生成・実行]  <--+
      | 単体テスト生成+実行        |
      | 結合テスト生成+実行        |
      | 失敗時 -> コード修正 ------+ (自己修正ループ)
      v
[Phase 4: ビルド設定生成]
      | Dockerfile
      | build scripts
      | -> generated/{project-name}/app/
      v
Complete
```

## Phase 1: 要件解析

### 入力
- `hearing/result.json`

### 解析対象フィールド
- `app_type`: アプリ種別 → アプリ構成の決定
- `language`: 言語 → 言語固有のプロジェクト構成
- `framework`: フレームワーク → フレームワーク固有のボイラープレート
- `compute_type`: デプロイ先 → Dockerfile/ビルド方式の決定
- `database`: DB有無 → DB接続コードの生成
- `sample_data`: サンプルデータ → シードデータ生成

## Phase 2: アプリコード生成

Claude Codeの生成能力でアプリケーションコードを生成する。
事前テンプレートは使用せず、要件に応じて毎回新規生成する。

### 生成対象
- メインアプリケーションコード
- API エンドポイント定義
- データモデル（DB使用時）
- DB接続・マイグレーション（DB使用時）
- サンプルデータシード（sample_data指定時）
- 設定ファイル（環境変数、ポート等）

### 出力先
- `generated/{project_name}/app/`

## Phase 3: テスト生成・実行

### 単体テスト
- ビジネスロジック、データモデルの単体テスト
- 言語標準のテストフレームワークを使用
- 生成後に即実行

### 結合テスト
- APIエンドポイントのテスト（テストクライアント使用）
- DB操作のテスト（DB使用時、テストDB/インメモリDB使用）
- 生成後に即実行

### 自己修正ループ
- テスト失敗時: エラー内容を分析 → コード修正 → テスト再実行
- 最大3回の修正ループ
- 修正不能な場合: 失敗テストの内容をユーザーに報告

## Phase 4: ビルド設定生成

### Dockerfile
- compute_typeに応じたDockerfile生成
- マルチステージビルド（ビルドステージ + 実行ステージ）
- 最小限のイメージサイズ

### OCI Functions固有
- func.yaml の生成（Functions使用時）

### ビルドスクリプト
- `build.sh` — ローカルビルド用スクリプト
