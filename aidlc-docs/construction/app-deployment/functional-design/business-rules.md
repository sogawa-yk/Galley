# Business Rules - Unit 5: App Deployment

## BR-1: ビルドルール
- Dockerfileが `generated/{project_name}/app/Dockerfile` に存在することを前提
- ビルドコマンド: `docker build -t {project_name}:latest generated/{project_name}/app/`
- ビルド失敗時: Dockerfileを修正して再ビルド（最大2回）

## BR-2: OCIRプッシュルール
- OCIR URL形式: `{region}.ocir.io/{tenancy_namespace}/{project_name}:latest`
- tenancy_namespaceはOCI CLIで取得: `oci os ns get`
- OCIRへのログイン: インスタンスプリンシパル認証（docker login不要、OCI CLI経由）

## BR-3: デプロイルール

### BR-3.1: OKEデプロイ
- kubeconfigをstack_outputsから取得・設定
- Kubernetes manifests（Deployment + Service + Ingress）を動的生成
- `kubectl apply -f` で適用
- Deployment rollout完了を待機

### BR-3.2: Container Instancesデプロイ
- 既存CIのimage_urlを更新、またはCIを新規作成
- OCI CLIでコンテナインスタンス操作

### BR-3.3: Computeデプロイ
- SSH経由でdocker pull + docker run
- ポート8080を公開

### BR-3.4: Functionsデプロイ
- OCI Functions CLI (fn) でデプロイ
- func.yaml使用

## BR-4: endpoints.json出力ルール
- 必須フィールド: `url`（アプリケーションのベースURL）
- オプション: `health_url`, `api_urls`, `compute_type`
- 例:
```json
{
  "url": "http://1.2.3.4:8080",
  "health_url": "http://1.2.3.4:8080/health",
  "compute_type": "container_instances",
  "project_name": "ecommerce-demo"
}
```

## BR-5: 自己修正ループ
- デプロイ失敗時: エラーログ分析 → manifests/設定修正 → 再デプロイ
- 最大2回リトライ
- 修正不能時: ユーザーに報告
