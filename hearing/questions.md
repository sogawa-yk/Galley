# Hearing Questions

**Generated from user request analysis**

**Extracted from request (questions skipped):**
- app_type: web (Webアプリ)
- language: nodejs (Node.js)
- framework: express (Express)
- compute_type: oke (OKE)
- database.type: mysql (MySQL)

---

## Question 1
このデモ環境のプロジェクト名を教えてください（英数字とハイフンのみ、例: task-manager-demo）。

A) 要望内容から自動で命名してほしい
B) 自分で指定する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
このデモ環境の主な目的を教えてください。

A) 顧客向け製品デモ
B) 技術検証・PoC
C) 社内トレーニング・ハンズオン
D) パフォーマンステスト
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
アプリケーションのコンテナ化方式を教えてください。

A) Dockerコンテナ
B) コンテナ不要（Compute VM上で直接実行）
C) OCI Functions（サーバーレス）
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
コンピュートリソースは新規作成しますか？既存のものを使いますか？

A) 新規作成する（デモ環境ごとに独立）
B) 既存の共有リソースを使用する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
コンピュートリソースのサイズを教えてください。

A) 最小構成（1 OCPU / 8GB RAM）-- デモ・検証向け
B) 標準構成（2 OCPU / 16GB RAM）
C) 大規模構成（4+ OCPU / 32GB+ RAM）
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 6
ネットワーク（VCN）の構成を教えてください。

A) 新規VCNを作成する
B) 既存のVCNを使用する
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 7
アプリケーションへのアクセス方式を教えてください。

A) パブリックアクセス（インターネットから直接アクセス）
B) プライベートアクセス（VPN/FastConnect経由のみ）
C) ロードバランサー経由のパブリックアクセス
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 8
以下の追加サービスが必要ですか？（複数選択可、カンマ区切りで回答）

A) Object Storage（ファイル保存）
B) Streaming / Queue（メッセージキュー）
C) API Gateway
D) Logging / Monitoring
E) 追加サービス不要
X) Other (please describe after [Answer]: tag below)

[Answer]: D

---

## Question 9
タスク管理ツールにサンプルデータ（タスク、ユーザー、プロジェクトなど）を事前投入しますか？

A) はい、デモ用のサンプルデータを投入してほしい
B) いいえ、空の状態で構築してほしい
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 10
フロントエンドの実装方式を教えてください。

A) サーバーサイドレンダリング（EJS/Pug等のテンプレートエンジン）
B) SPA（React/Vue.js等）+ Express APIバックエンド
C) シンプルなHTML/CSS/JavaScript（静的ファイル配信）
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 11
認証機能は必要ですか？

A) はい、ログイン機能が必要（ユーザー名/パスワード）
B) はい、OCI IAM / IDCS連携が必要
C) いいえ、認証不要（デモ用なのでオープンアクセス）
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 12
外部サービスとの連携は必要ですか？

A) はい、メール通知機能（OCI Email Delivery等）
B) はい、Slack/Teams等のチャットツール連携
C) はい、既存の社内システムとのAPI連携
D) いいえ、外部連携は不要
X) Other (please describe after [Answer]: tag below)

[Answer]: D
