# 設計書: ビルドインスタンスの追加

## アーキテクチャ

```
Galley (Container Instance, Resource Principal)
  │
  ├─ 1. app code を tar.gz にして Object Storage にアップロード
  │
  ├─ 2. oci instance-agent command create でビルドスクリプトを送信
  │     Target: Build Instance (Compute Instance)
  │
  │     Build Instance (Instance Principal):
  │       ├─ Object Storage から app code をダウンロード
  │       ├─ docker build -t <image_tag> .
  │       ├─ docker login (OCIR auth token)
  │       └─ docker push <image_uri>
  │
  ├─ 3. oci instance-agent command-execution get でポーリング
  │     → 完了待ち（exit_code, output取得）
  │
  ├─ 4. kubeconfig 取得 (既存: oci ce cluster create-kubeconfig)
  │
  └─ 5. kubectl apply (既存)
```

## Terraform変更 (deploy/)

### 新規ファイル

#### `deploy/build-instance.tf`
- `data "oci_core_images"` で Oracle Linux 8 の最新イメージを取得
- `oci_core_instance` (VM.Standard.E4.Flex, 1 OCPU, 8 GB)
- プライベートサブネット配置（NAT GW経由で外部通信）
- cloud-init で Docker Engine インストール
- Instance Agent Run Command プラグイン有効化

#### `deploy/iam.tf`
- `oci_identity_dynamic_group` — Build Instance を含む Dynamic Group
- `oci_identity_policy` — Object Storage 読取り権限（app code ダウンロード用）

### 変更ファイル

#### `deploy/variables.tf`
追加変数:
- `build_instance_ocpus` (default: 1)
- `build_instance_memory_in_gbs` (default: 8)
- `ocir_username` (string, OCIR ログイン用ユーザー名)
- `ocir_auth_token` (string, sensitive, OCIR ログイン用認証トークン)

#### `deploy/container-instance.tf`
環境変数追加:
- `GALLEY_BUILD_INSTANCE_ID` — Build Instance OCID
- `GALLEY_OCIR_ENDPOINT` — `<region>.ocir.io`
- `GALLEY_OCIR_USERNAME` — OCIR ユーザー名
- `GALLEY_OCIR_AUTH_TOKEN` — OCIR 認証トークン

#### `deploy/outputs.tf`
追加:
- `build_instance_id` — Build Instance OCID

## Python変更

### `src/galley/config.py`
新規フィールド:
```python
build_instance_id: str = ""      # GALLEY_BUILD_INSTANCE_ID
ocir_endpoint: str = ""           # GALLEY_OCIR_ENDPOINT
ocir_username: str = ""           # GALLEY_OCIR_USERNAME
ocir_auth_token: str = ""         # GALLEY_OCIR_AUTH_TOKEN
bucket_name: str = ""             # GALLEY_BUCKET_NAME (既存env var)
bucket_namespace: str = ""        # GALLEY_BUCKET_NAMESPACE (既存env var)
region: str = ""                  # GALLEY_REGION (既存env var)
```

### `src/galley/services/app.py`
AppServiceのコンストラクタを拡張し、configを受け取る。

新規メソッド:
- `_upload_app_tarball(session_id) -> str` — app dir を tar.gz にして Object Storage にアップロード
- `_build_and_push_image(session_id) -> str` — instance-agent 経由でビルド、image_uri を返す
- `_wait_for_command(command_id, instance_id) -> tuple[int, str]` — コマンド完了をポーリング

`build_and_deploy`の変更:
- `image_uri` をオプショナル化
- 未指定時: `_upload_app_tarball` → `_build_and_push_image` → 既存デプロイフロー
- 指定時: 既存フロー（kubectl apply 直行）

### `src/galley/tools/app.py`
- `image_uri` パラメータを `str | None = None` に変更
- docstring更新

### `src/galley/server.py`
- `AppService` に config を渡すように変更

## OCIR認証方式

MVP段階ではユーザーがTerraform変数として提供する認証トークンを使用:
- `ocir_username`: `<namespace>/oracleidentitycloudservice/<email>`
- `ocir_auth_token`: OCI Console → User Settings → Auth Tokens で生成

ビルドスクリプト内で `docker login` に使用する。

## instance-agent command のJSON構造

### Content (inline script, < 4KB)
```json
{
  "source": {
    "sourceType": "TEXT",
    "text": "#!/bin/bash\nset -e\n..."
  }
}
```

### Target
```json
{
  "instanceId": "<build_instance_ocid>"
}
```

### 完了チェック
```bash
oci instance-agent command-execution get \
  --command-id <command_id> \
  --instance-id <instance_id>
```
レスポンスの `lifecycleState` が `SUCCEEDED` / `FAILED` になるまでポーリング。
