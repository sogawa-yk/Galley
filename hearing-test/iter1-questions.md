# Hearing Questions

以下の質問に回答してください。各質問の [Answer]: タグの後に選択肢の文字を記入してください。

---

## Question 1
このデモ環境のプロジェクト名を教えてください（英数字とハイフンのみ、例: inventory-api-demo）。

A) 要望内容から自動で命名してほしい
B) 自分で指定する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
アプリケーションのコンテナ化方式を教えてください。

A) Dockerコンテナ
B) コンテナ不要（Compute VM上で直接実行）
C) OCI Functions（サーバーレス）
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 3
コンピュートリソースは新規作成しますか？既存のものを使いますか？

A) 新規作成する（デモ環境ごとに独立）
B) 既存の共有リソースを使用する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
コンピュートリソースのサイズを教えてください。

A) 最小構成（1 OCPU / 8GB RAM）— デモ・検証向け
B) 標準構成（2 OCPU / 16GB RAM）
C) 大規模構成（4+ OCPU / 32GB+ RAM）
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
ネットワーク（VCN）の構成を教えてください。

A) 新規VCNを作成する
B) 既存のVCNを使用する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6
在庫管理APIにサンプルデータ（商品マスタ、在庫データなど）を投入しますか？

A) はい、基本的なサンプルデータを自動生成してほしい
B) いいえ、空の状態で構築してほしい
C) 自分でデータを用意する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 7
在庫管理APIに認証機能は必要ですか？

A) 不要（オープンアクセス）
B) APIキー認証
C) OAuth2/OIDC認証
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 8
以下の追加サービスが必要ですか？（複数選択可、カンマ区切りで回答）

A) Object Storage（ファイル保存）
B) Streaming / Queue（メッセージキュー）
C) API Gateway
D) Logging / Monitoring
E) 追加サービス不要
X) Other (please describe after [Answer]: tag below)

[Answer]: E
