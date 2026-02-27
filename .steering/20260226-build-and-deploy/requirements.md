# 要求仕様

## 元フィードバック
`docs/feedbacks/20260226-2.md` — C1: `build_and_deploy`が未実装

## PRD参照
- F12: アプリケーションカスタマイズとデプロイ
- `galley:build_and_deploy` でビルド→OCIR push→OKEデプロイを一括実行できる

## 対応スコープ

### build_and_deploy の実装
- OKEクラスタへのアプリケーションデプロイ機能を実装する
- K8sマニフェスト（Deployment + Service）を自動生成する
- `oci ce cluster create-kubeconfig` でkubeconfig を取得する
- `kubectl apply` でデプロイを実行する
- `kubectl rollout status` でデプロイ完了を確認する
- デプロイ後のエンドポイント（LoadBalancer IP）を返却する

### パラメータ拡張
- `cluster_id`: OKEクラスタOCID（必須）
- `image_uri`: コンテナイメージURI（必須 — ビルドは将来対応）
- `namespace`: K8s名前空間（デフォルト: "default"）

### check_app_status の実装
- `kubectl get deployment` でデプロイ状態を確認する
- `kubectl get svc` でエンドポイントを取得する

### スコープ外
- Docker イメージビルド（Galleyコンテナ内にDockerデーモンがないため）
- OCIR push（ビルドと連動するため同時に将来対応）
- 自動ロールバック（MVP後に対応）
- ヘルスチェック（MVP後に対応）
