# 要求内容

## 概要

ヒアリングセッションを開始した際に、セッションIDをユーザーに必ず明示的に返すようにする。
現在、他のツール（`save_answer`, `complete_hearing`, `save_architecture`等）がsession_idを引数として要求するが、ユーザーからはそのIDが不明な状態。

## 問題

1. `start_hearing`プロンプトがセッション作成後にsession_idを明示的にユーザーに伝えるよう指示していない
2. `create_session`ツールの戻り値にはsession_idが含まれるが、LLMがそれをユーザーに伝えるかは保証されない

## 解決方針

`start_hearing`プロンプトを改善し、セッション作成後にsession_idをユーザーに必ず表示するよう指示を追加する。
