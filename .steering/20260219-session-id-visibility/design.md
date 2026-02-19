# 設計

## 変更対象

### `src/galley/prompts/hearing.py`

`start_hearing`プロンプトの手順テキストを修正:
- ステップ1でセッション作成後、**session_idをユーザーに必ず提示する**よう明記
- 他のツール呼び出し時にsession_idが必要であることを注意事項に追加

## 影響範囲

- プロンプトテキストの変更のみ
- サービス層・モデル層・ツール層の変更なし（`create_session`は既にsession_idを返している）
- 既存テストへの影響: `test_list_prompts_via_mcp`は名前チェックのみなので影響なし
