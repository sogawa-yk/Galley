# 要求仕様

## 元フィードバック
`docs/feedbacks/20260227-oke-api-port6443.md`

## 要求

OKEコンポーネントが存在するアーキテクチャで `export_iac` を実行した場合、Public Security Listに Kubernetes API Server (TCP port 6443) への外部アクセスルールが自動生成されること。

### 背景
- OKEクラスタの `endpoint_config.is_public_ip_enabled = true` によりAPI ServerはPublic SubnetにPublic IPで公開される
- kubectlによる外部からのクラスタ操作（`build_and_deploy` 含む）にはport 6443が必要
- 現状はport 443のみ許可されており、6443が欠落

### 受入条件
1. OKE構成でPublic SLにTCP 6443 from 0.0.0.0/0のingressルールが含まれること
2. Private SLにはport 6443ルールが追加されないこと（API ServerはPublic Subnetにのみ存在）
3. OKEなし構成ではport 6443ルールが含まれないこと
4. 既存テストが全てパスすること
