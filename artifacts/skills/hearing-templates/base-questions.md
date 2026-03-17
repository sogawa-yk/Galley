# Hearing Base Question Templates

このファイルは hearing.md Skill が参照する質問テンプレートです。
各カテゴリの質問をユーザーの要望に応じて選択・カスタマイズして使用します。

---

## Category: project_info (常に必須)

### Q: プロジェクト名
このデモ環境のプロジェクト名を教えてください（英数字とハイフンのみ、例: ecommerce-demo）。

A) 要望内容から自動で命名してほしい
B) 自分で指定する
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

### Q: デモの目的
このデモ環境の主な目的を教えてください。

A) 顧客向け製品デモ
B) 技術検証・PoC
C) 社内トレーニング・ハンズオン
D) パフォーマンステスト
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

## Category: app_type (常に必須)

### Q: アプリケーション種別
構築するアプリケーションの種別を教えてください。

A) Webアプリケーション（フロントエンド + バックエンドAPI）
B) REST APIサーバーのみ
C) バッチ処理アプリケーション
D) マイクロサービス（複数サービス構成）
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

### Q: プログラミング言語
アプリケーションのプログラミング言語を教えてください。

A) Python (Flask/FastAPI)
B) Java (Spring Boot)
C) Node.js (Express/NestJS)
D) Go (Gin/Echo)
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

### Q: コンテナ化
アプリケーションのコンテナ化方式を教えてください。

A) Dockerコンテナ
B) コンテナ不要（Compute VM上で直接実行）
C) OCI Functions（サーバーレス）
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

## Category: infra_config (常に必須)

### Q: コンピュート種別
アプリケーションの実行環境を教えてください。

A) OKE (Oracle Kubernetes Engine) — Kubernetesクラスター
B) Container Instances — マネージドコンテナ
C) Compute Instance — 仮想マシン
D) OCI Functions — サーバーレス
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

### Q: コンピュート作成方針
コンピュートリソースは新規作成しますか？既存のものを使いますか？

A) 新規作成する（デモ環境ごとに独立）
B) 既存の共有リソースを使用する
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

### Q: サイジング
コンピュートリソースのサイズを教えてください。

A) 最小構成（1 OCPU / 8GB RAM）— デモ・検証向け
B) 標準構成（2 OCPU / 16GB RAM）
C) 大規模構成（4+ OCPU / 32GB+ RAM）
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

## Category: database (条件付き)

### Q: データベース種別
データベースは必要ですか？必要な場合、種別を教えてください。

A) Autonomous Database (ATP) — フルマネージド
B) MySQL Database Service
C) NoSQL Database (Oracle NoSQL)
D) データベース不要
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

## Category: network (条件付き)

### Q: VCN構成
ネットワーク（VCN）の構成を教えてください。

A) 新規VCNを作成する
B) 既存のVCNを使用する
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

### Q: アクセス方式
アプリケーションへのアクセス方式を教えてください。

A) パブリックアクセス（インターネットから直接アクセス）
B) プライベートアクセス（VPN/FastConnect経由のみ）
C) ロードバランサー経由のパブリックアクセス
X) Other (please describe after [Answer]: tag below)

[Answer]:

---

## Category: additional_services (条件付き)

### Q: 追加サービス
以下の追加サービスが必要ですか？（複数選択可、カンマ区切りで回答）

A) Object Storage（ファイル保存）
B) Streaming / Queue（メッセージキュー）
C) API Gateway
D) Logging / Monitoring
E) 追加サービス不要
X) Other (please describe after [Answer]: tag below)

[Answer]:
