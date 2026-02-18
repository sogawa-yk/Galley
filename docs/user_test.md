# ユーザーテスト手順書

MVP（F1: MCPサーバー基盤 + F2: ヒアリングセッション管理）の動作を検証するための手順書です。

## 前提条件

```bash
# 依存関係のインストール（未実施の場合）
uv sync --all-extras
```

---

## 1. 自動テストの実行

まず、自動テストで基本的な品質を確認します。

### 1-1. 全テスト実行

```bash
uv run pytest -v
```

**期待結果**: 39件のテストが全てパス（`39 passed`）

### 1-2. カバレッジ付きテスト実行

```bash
uv run pytest --cov=galley --cov-report=term-missing
```

**確認ポイント**: 各モジュールのカバレッジ率を確認

### 1-3. コード品質チェック

```bash
uv run ruff check .           # リントチェック
uv run ruff format --check .  # フォーマットチェック
uv run mypy src/              # 型チェック
```

**期待結果**: 全てエラーなし

---

## 2. MCPサーバーの起動確認

### 2-1. stdioモードでの起動確認

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1.0"}}}' | uv run python -m galley
```

**期待結果**: JSON-RPCレスポンス（`result` に `serverInfo` や `capabilities` が含まれる）が標準出力に返される

---

## 3. Pythonスクリプトによる手動テスト

FastMCPの `Client` を使って、MCPプロトコル経由でツールを呼び出します。

### 3-1. テストスクリプトの実行

以下のコマンドを実行してください:

```bash
uv run python -c "
import asyncio
import json
from pathlib import Path
from fastmcp import Client
from galley.config import ServerConfig
from galley.server import create_server

async def main():
    # テスト用の一時ディレクトリでサーバーを起動
    config = ServerConfig(data_dir=Path('/tmp/galley-user-test'))
    server = create_server(config)

    async with Client(server) as client:
        # ============================
        # ツール一覧の確認
        # ============================
        print('=== ツール一覧 ===')
        tools = await client.list_tools()
        for t in tools:
            print(f'  - {t.name}: {t.description[:60]}...')
        print()

        # ============================
        # リソース一覧の確認
        # ============================
        print('=== リソース一覧 ===')
        resources = await client.list_resources()
        for r in resources:
            print(f'  - {r.uri}: {r.name}')
        print()

        # ============================
        # プロンプト一覧の確認
        # ============================
        print('=== プロンプト一覧 ===')
        prompts = await client.list_prompts()
        for p in prompts:
            print(f'  - {p.name}: {p.description[:60]}...')
        print()

        # ============================
        # ヒアリングフロー全体テスト
        # ============================
        print('=== ヒアリングフロー開始 ===')
        print()

        # Step 1: セッション作成
        result = await client.call_tool('create_session', {})
        data = json.loads(result.content[0].text)
        session_id = data['session_id']
        print(f'[Step 1] セッション作成: session_id={session_id}, status={data[\"status\"]}')

        # Step 2: 単件回答保存
        result = await client.call_tool('save_answer', {
            'session_id': session_id,
            'question_id': 'purpose',
            'value': 'REST APIとデータベースを使ったWebアプリケーション',
        })
        data = json.loads(result.content[0].text)
        print(f'[Step 2] 回答保存(単件): question_id={data[\"question_id\"]}')

        # Step 3: バッチ回答保存
        result = await client.call_tool('save_answers_batch', {
            'session_id': session_id,
            'answers': [
                {'question_id': 'users', 'value': '1000人程度'},
                {'question_id': 'workload_type', 'value': 'Webアプリケーション'},
                {'question_id': 'database_required', 'value': 'Autonomous Database (ATP)'},
                {'question_id': 'network_requirements', 'value': 'パブリックアクセスが必要、API GatewayでHTTPS終端'},
                {'question_id': 'security_requirements', 'value': 'TLS暗号化、IAMによるアクセス制御'},
                {'question_id': 'availability_requirements', 'value': '99.9% SLA'},
                {'question_id': 'budget_constraints', 'value': '月額10万円以内'},
                {'question_id': 'timeline', 'value': '2週間以内'},
                {'question_id': 'additional_notes', 'value': 'OKEでのコンテナ運用を希望'},
            ],
        })
        data = json.loads(result.content[0].text)
        print(f'[Step 3] 回答保存(バッチ): saved_count={data[\"saved_count\"]}')

        # Step 4: ヒアリング完了
        result = await client.call_tool('complete_hearing', {
            'session_id': session_id,
        })
        data = json.loads(result.content[0].text)
        print(f'[Step 4] ヒアリング完了: session_id={data[\"session_id\"]}')
        print(f'         requirements数: {len(data[\"requirements\"])}')
        print(f'         constraints数: {len(data[\"constraints\"])}')
        print()

        # Step 5: ヒアリング結果取得
        result = await client.call_tool('get_hearing_result', {
            'session_id': session_id,
        })
        data = json.loads(result.content[0].text)
        print(f'[Step 5] ヒアリング結果取得:')
        print(f'         summary冒頭: {data[\"summary\"][:80]}...')
        print()

        # ============================
        # リソース読み取りテスト
        # ============================
        print('=== リソース読み取り ===')
        questions = await client.read_resource('galley://hearing/questions')
        print(f'  hearing/questions: {len(str(questions))} bytes')
        flow = await client.read_resource('galley://hearing/flow')
        print(f'  hearing/flow: {len(str(flow))} bytes')
        print()

        # ============================
        # エラーハンドリングテスト
        # ============================
        print('=== エラーハンドリング ===')

        # 存在しないセッションへのアクセス
        result = await client.call_tool('save_answer', {
            'session_id': 'nonexistent-session',
            'question_id': 'purpose',
            'value': 'test',
        }, raise_on_error=False)
        data = json.loads(result.content[0].text)
        print(f'  存在しないセッション: error={data.get(\"error\")}, message={data.get(\"message\")}')

        # 完了済みセッションへの回答保存
        result = await client.call_tool('save_answer', {
            'session_id': session_id,
            'question_id': 'purpose',
            'value': 'test',
        }, raise_on_error=False)
        data = json.loads(result.content[0].text)
        print(f'  完了済みセッション: error={data.get(\"error\")}, message={data.get(\"message\")}')

        # 未完了セッションの結果取得
        new_result = await client.call_tool('create_session', {})
        new_data = json.loads(new_result.content[0].text)
        new_sid = new_data['session_id']
        result = await client.call_tool('get_hearing_result', {
            'session_id': new_sid,
        }, raise_on_error=False)
        data = json.loads(result.content[0].text)
        print(f'  未完了セッション結果取得: error={data.get(\"error\")}, message={data.get(\"message\")}')
        print()

        print('=== 全テスト完了 ===')

asyncio.run(main())
"
```

### 3-2. 期待される出力

```
=== ツール一覧 ===
  - create_session: 新しいヒアリングセッションを作成する。...
  - save_answer: ヒアリング回答を保存する。...
  - save_answers_batch: 複数のヒアリング回答を一括保存する。...
  - complete_hearing: ヒアリングを完了し、構造化された結果を生成する。...
  - get_hearing_result: ヒアリング結果を取得する。...

=== リソース一覧 ===
  - galley://hearing/questions: ...
  - galley://hearing/flow: ...

=== プロンプト一覧 ===
  - start_hearing: ...
  - resume_hearing: ...

=== ヒアリングフロー開始 ===

[Step 1] セッション作成: session_id=<UUID>, status=in_progress
[Step 2] 回答保存(単件): question_id=purpose
[Step 3] 回答保存(バッチ): saved_count=9
[Step 4] ヒアリング完了: session_id=<UUID>
         requirements数: 6
         constraints数: 4

[Step 5] ヒアリング結果取得:
         summary冒頭: # ヒアリング結果サマリー...

=== リソース読み取り ===
  hearing/questions: <バイト数> bytes
  hearing/flow: <バイト数> bytes

=== エラーハンドリング ===
  存在しないセッション: error=SessionNotFoundError, message=...
  完了済みセッション: error=HearingAlreadyCompletedError, message=...
  未完了セッション結果取得: error=HearingNotCompletedError, message=...

=== 全テスト完了 ===
```

### 3-3. 確認ポイント

| 項目 | 確認内容 |
|------|---------|
| ツール登録 | 5つのツール（create_session, save_answer, save_answers_batch, complete_hearing, get_hearing_result）が表示される |
| リソース登録 | 2つのリソース（galley://hearing/questions, galley://hearing/flow）が表示される |
| プロンプト登録 | 2つのプロンプト（start_hearing, resume_hearing）が表示される |
| セッション作成 | UUID形式のsession_idが返される |
| 回答保存(単件) | question_idが正しく返される |
| 回答保存(バッチ) | saved_countが9になる |
| ヒアリング完了 | requirements, constraintsが構造化されて返される |
| 結果取得 | 保存された回答がサマリーに反映されている |
| エラー: 不正セッション | `SessionNotFoundError` が返される |
| エラー: 完了済みセッション | `HearingAlreadyCompletedError` が返される |
| エラー: 未完了結果取得 | `HearingNotCompletedError` が返される |

---

## 4. データ永続化の確認

テストスクリプト実行後、ファイルシステムにセッションデータが保存されていることを確認します。

```bash
# セッションディレクトリの一覧
ls /tmp/galley-user-test/sessions/

# セッションデータの中身を確認（最初に見つかったセッション）
SESSION_DIR=$(ls /tmp/galley-user-test/sessions/ | head -1)
cat /tmp/galley-user-test/sessions/$SESSION_DIR/session.json | python -m json.tool
```

### 確認ポイント

- `sessions/` ディレクトリ配下にUUID名のサブディレクトリが作成されている
- `session.json` に以下のフィールドが含まれる:
  - `id`: UUID文字列
  - `status`: `"completed"`
  - `answers`: 10個の質問IDと回答のマッピング
  - `hearing_result`: 構造化されたヒアリング結果（summary, requirements, constraints）
  - `created_at`, `updated_at`: ISO 8601形式のタイムスタンプ

---

## 5. テスト後のクリーンアップ

```bash
rm -rf /tmp/galley-user-test
```

---

## テスト結果の判定基準

| 判定 | 条件 |
|------|------|
| **合格** | セクション1〜4の全確認ポイントをクリア |
| **不合格** | いずれかの確認ポイントで期待結果と異なる |

不合格の場合は、エラーメッセージとともに開発チームに報告してください。
