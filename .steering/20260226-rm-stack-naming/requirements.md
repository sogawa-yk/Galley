# 要件: RMスタック命名改善

## 概要

Resource Managerスタック作成時の`display_name`を、Galley起源であることと目的がわかるように改善する。

## 現状

- `display_name=f"galley-{session_id}"` (例: `galley-a1b2c3d4-e5f6-...`)
- UUID文字列のため、OCI Consoleで見た際に何のスタックかわからない

## 要件

1. スタック名にGalley起源であることを示すプレフィックスを維持する
2. ヒアリングで回答された`purpose`（目的）をスタック名に含める
3. OCI display_nameの制限（255文字）を超えない
4. purposeが未設定の場合は従来通りsession_idでフォールバック
5. display_nameに使えない文字を適切にサニタイズする
