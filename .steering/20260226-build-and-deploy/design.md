# 設計

## アーキテクチャ判断

### Docker ビルドをスコープ外にする理由
GalleyコンテナにはDockerデーモンが含まれていない（Container Instance内でDocker-in-Dockerは不可）。
buildah/kaniko等のルートレスビルダーの追加はDockerfile変更が必要で、本タスクの主目的ではない。
代わりに `image_uri` パラメータで事前ビルド済みイメージを受け取る設計とする。

### AppServiceがInfraServiceの_run_subprocessパターンを再利用
subprocess実行のパターン（`asyncio.create_subprocess_exec`）はInfraServiceと同一。
AppServiceに同様のヘルパーメソッドを追加する。InfraServiceとの共有は、
サービス間依存を避けるため行わない（レイヤー設計の原則に従う）。

## 変更対象ファイル

### 変更
| ファイル | 変更内容 |
|---------|---------|
| `src/galley/services/app.py` | `build_and_deploy` / `check_app_status` を実装、K8sマニフェスト生成 |
| `src/galley/tools/app.py` | `build_and_deploy` のパラメータ拡張（cluster_id, image_uri, namespace） |
| `src/galley/models/app.py` | `DeployResult` にK8s関連フィールド追加 |
| `tests/unit/services/test_app.py` | テスト更新・追加 |

### 新規作成なし

## build_and_deploy フロー

```
1. セッション検証（session存在、app scaffolded済み）
2. アプリ情報の取得（template-metadata.json → app_port等）
3. K8sマニフェスト生成（Deployment + Service YAML）
   - {session_dir}/k8s/ に書き出し
4. kubeconfig取得
   - `oci ce cluster create-kubeconfig --cluster-id {cluster_id} --file {kubeconfig_path} --token-version 2.0.0`
5. kubectl apply
   - `kubectl apply -f {k8s_dir} --kubeconfig {kubeconfig_path}`
6. rollout status待ち
   - `kubectl rollout status deployment/{app_name} --kubeconfig {kubeconfig_path} --timeout 300s`
7. エンドポイント取得
   - `kubectl get svc {app_name} --kubeconfig {kubeconfig_path} -o jsonpath='{.status.loadBalancer.ingress[0].ip}'`
8. DeployResult返却
```

## K8sマニフェストテンプレート

### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  namespace: {namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
        - name: {app_name}
          image: {image_uri}
          ports:
            - containerPort: {app_port}
```

### service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {app_name}
  namespace: {namespace}
spec:
  type: LoadBalancer
  selector:
    app: {app_name}
  ports:
    - port: 80
      targetPort: {app_port}
      protocol: TCP
```

## ツールインターフェース変更

```python
@mcp.tool()
async def build_and_deploy(
    session_id: str,
    cluster_id: str,
    image_uri: str,
    namespace: str = "default",
) -> dict[str, Any]:
    """ビルド・デプロイを一括実行する。

    スキャフォールドされたアプリケーションをOKEクラスタにデプロイします。
    K8sマニフェスト（Deployment + Service）を自動生成し、
    kubectl applyでデプロイを実行します。

    Args:
        session_id: セッションID。
        cluster_id: OKEクラスタのOCID。
        image_uri: コンテナイメージURI（例: ghcr.io/user/app:latest）。
        namespace: K8s名前空間（デフォルト: default）。
    """
```
