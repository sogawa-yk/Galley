# Requirements Verification Questions

以下の質問に回答してください。各質問の `[Answer]:` タグの後に選択肢の文字を記入してください。
選択肢に合うものがない場合は、最後の「Other」を選び、説明を追記してください。

---

## Question 1

このシステムの主な対象クラウドプロバイダーはどれですか？

A) AWS
B) Oracle Cloud Infrastructure (OCI)
C) Google Cloud Platform (GCP)
D) Microsoft Azure
E) マルチクラウド（複数プロバイダー対応）
F) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 2

自然言語からインフラを構築する際のIaC（Infrastructure as Code）ツールはどれを使用しますか？

A) Terraform
B) AWS CloudFormation
C) Pulumi
D) Ansible
E) Other (please describe after [Answer]: tag below)

[Answer]: Terraform

## Question 3

対応するAIクライアントの優先順位を教えてください。最も重要なものを選択してください。

A) Claude Code（CLI）が最優先
B) Claude Desktop（MCP経由）が最優先
C) ChatGPT（API/プラグイン）が最優先
D) すべて同等に対応する
E) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4

システムのアーキテクチャパターンはどのようなものを想定していますか？

A) MCPサーバー型 — AIクライアントがMCPプロトコルでバックエンドと通信
B) REST API型 — 汎用的なAPIサーバーとして構築し、各クライアントからHTTPで呼び出す
C) CLI型 — コマンドラインツールとして構築
D) ハイブリッド型 — MCPサーバー + REST API両方を提供
E) Other (please describe after [Answer]: tag below)

[Answer]: Skills, worlflows型（OCI上にインスタンスプリンシパル認証を受けたインスタンスを立てて、その上にインストールしたociコマンドを利用してOCI操作を行います）

## Question 5

デプロイ対象のアプリケーションの種類は何ですか？

A) Webアプリケーション（コンテナベース）
B) サーバーレスアプリケーション（Lambda/Functions）
C) Kubernetes上のマイクロサービス
D) 上記すべてに対応する汎用的なシステム
E) Other (please describe after [Answer]: tag below)

[Answer]: D

## Question 6

インフラ構築の自動化レベルはどの程度を想定していますか？

A) 完全自動 — 自然言語の指示だけでインフラを構築・デプロイまで実行
B) 半自動 — IaCコードを生成し、ユーザーがレビュー後に適用
C) アシスタント型 — IaCコードと手順書を生成し、ユーザーが手動で実行
D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 7

このシステムの開発言語として何を使用しますか？

A) Python
B) TypeScript/Node.js
C) Go
D) Python + TypeScript（バックエンド + フロントエンド）
E) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 8

このプロジェクトの用途・目的はどれに最も近いですか？

A) 本番運用を見据えたプロダクション品質のシステム
B) PoC（概念実証）/ プロトタイプ
C) 社内ツール / 開発効率化ツール
D) 学習・研究目的
E) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 9

認証・セキュリティの要件はどの程度ですか？

A) 高 — IAM統合、監査ログ、RBAC、暗号化が必要
B) 中 — APIキー認証と基本的なアクセス制御
C) 低 — 個人利用のため最小限のセキュリティ
D) Other (please describe after [Answer]: tag below)

[Answer]: インスタンスプリンシパル認証済みのインスタンス上で実行するOCIコマンドを利用するため、ツール側での認証・セキュリティ要件はありません

## Question: Security Extensions

Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)
B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)
X) Other (please describe after [Answer]: tag below)

[Answer]: B
