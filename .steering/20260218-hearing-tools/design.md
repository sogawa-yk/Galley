# 設計書

## アーキテクチャ概要

既存のMCPリソースと同じデータソース（`config/*.yaml`）を、MCPツールとしても公開する。リソースは削除せず並存させる。

```
MCPクライアント
  ├─ ツール呼び出し: get_hearing_questions → config/hearing-questions.yaml
  ├─ ツール呼び出し: get_hearing_flow    → config/hearing-flow.yaml
  └─ リソース読取:   galley://hearing/*   → 同上（既存、維持）
```

## コンポーネント設計

### 1. ヒアリングツール（`src/galley/tools/hearing.py`）

**変更内容**:
- `register_hearing_tools` に `config_dir` キーワード引数を追加
- `get_hearing_questions` ツールを追加: YAMLファイルを読み込みdictで返却
- `get_hearing_flow` ツールを追加: 同上

**実装の要点**:
- 既存リソース（`src/galley/resources/hearing.py`）はYAMLをstringで返すが、ツールはYAMLをパースしたdictで返す（ツール結果はJSON直列化されるため）
- `config_dir` が未設定の場合はエラーdictを返す（防御的プログラミング）

### 2. ヒアリングプロンプト（`src/galley/prompts/hearing.py`）

**変更内容**:
- `start_hearing`: 手順2,3の`galley://hearing/*`リソース参照を`get_hearing_questions`/`get_hearing_flow`ツール呼び出しに変更
- `resume_hearing`: 手順1の同様の変更

### 3. サーバー初期化（`src/galley/server.py`）

**変更内容**:
- `register_hearing_tools` 呼び出しに `config_dir=config.config_dir` を追加

## データフロー

### ヒアリング開始フロー（修正後）
```
1. ユーザー: start_hearing プロンプトを選択
2. Claude: プロンプトテキストに従い get_hearing_questions ツールを呼び出し
3. Galley: config/hearing-questions.yaml を読み込みdictで返却
4. Claude: get_hearing_flow ツールを呼び出し
5. Galley: config/hearing-flow.yaml を読み込みdictで返却
6. Claude: フローに従ってユーザーに質問を提示
```

## テスト戦略

### 回帰テスト
- 既存unit tests（67件）: 変更なし、全パス確認
- 既存integration tests（20件）: 変更なし、全パス確認

### 手動検証
- ローカル: `create_server()` でツール数17を確認
- リモート: curl MCP tools/list で17ツール返却を確認
- Claude Desktop: ヒアリング開始が正常に動作することを確認

## 変更ファイル一覧

```
src/galley/tools/hearing.py    # get_hearing_questions, get_hearing_flow 追加
src/galley/prompts/hearing.py  # リソース参照→ツール参照に変更
src/galley/server.py           # register_hearing_tools に config_dir 追加
```

## 実装の順序

1. `tools/hearing.py` にツール追加（`config_dir` 引数追加、2ツール実装）
2. `server.py` の呼び出し元を修正
3. `prompts/hearing.py` のプロンプトテキストを修正
4. pytest全テスト実行
5. ツール数確認（15→17）
6. コミット・OCIRプッシュ・Container Instance再起動
7. リモート検証
