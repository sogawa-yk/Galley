# 設計: RMスタック命名改善

## 変更方針

`_ensure_rm_stack()`内のdisplay_name生成ロジックを変更する。

### 命名パターン

```
galley-{purpose_slug}-{session_id_short}
```

例:
- `galley-rest-api-a1b2c3d4` (purpose="REST API構築")
- `galley-iot-platform-f5e6d7c8` (purpose="IoTリアルタイムデータ分析プラットフォーム")
- `galley-a1b2c3d4` (purposeが未設定の場合のフォールバック)

### display_name生成ロジック

1. `session.answers`から`purpose`の回答値を取得
2. 日本語含むテキストをASCIIスラッグに変換（`re.sub`で非英数字をハイフンに）
3. スラッグを最大40文字に切り詰め
4. session_idの先頭8文字をサフィックスとして付与（一意性確保）
5. 全体が255文字を超えないことを保証

### 変更ファイル

- `src/galley/services/infra.py`: `_ensure_rm_stack()`内のdisplay_name生成 + ヘルパーメソッド追加
- `tests/unit/services/test_infra.py`: display_nameの検証テスト追加
