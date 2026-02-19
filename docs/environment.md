# 環境情報 (Environment Reference)

開発・デプロイに必要な環境固有の情報をまとめたドキュメント。

## OCI 基本情報

| 項目 | 値 | 備考 |
|------|-----|------|
| リージョン | `ap-osaka-1` | |
| コンパートメントOCID | `ocid1.compartment.oc1..aaaaaaaanxm4oucgt5pkgd7sw2vouvckvvxan7ca2lirowaao7krnzlkdkhq` | Galleyインフラ配置先 |
| 作業対象コンパートメントOCID | 同上（未指定時はcompartment_ocidと同じ） | Galleyが操作するリソースの配置先 |
| Object Storageネームスペース | `orasejapan` | `oci os ns get` で確認 |

## コンテナイメージ

| 項目 | 値 |
|------|-----|
| OCIR リポジトリURL | `kix.ocir.io/{namespace}/galley` |
| イメージタグ規則 | `latest` または任意のバージョンタグ |
| ビルドコマンド | `docker build -f docker/Dockerfile -t galley .` |
| タグ付け | `docker tag galley {OCIR_URL}:{tag}` |
| プッシュ | `docker push {OCIR_URL}:{tag}` |

### OCIR認証
すでに認証済みなので実施は不要
```bash
# OCIRへのログイン
docker login kix.ocir.io -u '{namespace}/{username}'
```

## デプロイ済みリソース

> Terraform state から取得する値。初回 `terraform apply` 後に記入する。

| リソース | OCID / 値 | 備考 |
|----------|-----------|------|
| Container Instance | `ocid1.containerinstance.oc1...` | |
| API Gateway | `ocid1.apigateway.oc1...` | |
| API Gateway ホスト名 | `https://xxx.apigateway.ap-osaka-1.oci.customer-oci.com` | |
| URLトークン | （Terraform output参照） | `terraform output url_token` |
| MCP エンドポイント | `https://{hostname}/mcp?token={token}` | Claude Desktop設定に使用 |
| VCN | `ocid1.vcn.oc1...` | |
| Object Storage バケット | `galley-xxxxxxxx` | |

### Terraform output で一括確認

```bash
cd deploy/
terraform output
```

## 環境変数一覧

### アプリケーション設定（`GALLEY_` プレフィックス）

| 変数名 | 型 | デフォルト | コンテナ内 | 説明 |
|--------|-----|-----------|-----------|------|
| `GALLEY_HOST` | str | `0.0.0.0` | `0.0.0.0` | サーバーバインドアドレス |
| `GALLEY_PORT` | int | `8000` | `8000` | サーバーポート |
| `GALLEY_DATA_DIR` | Path | `{repo}/.galley` | `/data` | セッションデータ保存先 |
| `GALLEY_CONFIG_DIR` | Path | `{repo}/config` | `/app/config` | 設定ファイルディレクトリ |
| `GALLEY_URL_TOKEN` | str | `""` (認証なし) | Terraform自動生成(32文字) | URL認証トークン |
| `GALLEY_BUCKET_NAME` | str | - | Terraform自動設定 | Object Storageバケット名 |
| `GALLEY_BUCKET_NAMESPACE` | str | - | Terraform自動設定 | Object Storageネームスペース |
| `GALLEY_REGION` | str | - | Terraform自動設定 | OCIリージョン |

### ローカル開発時

ローカルでは `GALLEY_BUCKET_*` / `GALLEY_REGION` は不要（ファイルシステムベースで動作）。

```bash
# 最小構成で起動
python -m galley

# トークン認証を有効にして起動
GALLEY_URL_TOKEN=mysecret python -m galley
```

## Terraform 入力変数

| 変数 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `compartment_ocid` | string | Yes | - | インフラ配置コンパートメントOCID |
| `region` | string | Yes | - | OCIリージョン |
| `galley_work_compartment_id` | string | No | `compartment_ocid` | 作業対象コンパートメント |
| `image_tag` | string | No | `latest` | コンテナイメージタグ |
| `galley_image_url` | string | No | 自動生成 | イメージフルURL（OCIR自動構成を上書き） |
| `container_instance_shape` | string | No | `CI.Standard.E4.Flex` | Container Instanceシェイプ |
| `container_instance_ocpus` | number | No | `1` | OCPU数 |
| `container_instance_memory_in_gbs` | number | No | `2` | メモリ(GB) |

### `terraform.tfvars` の例

```hcl
compartment_ocid = "ocid1.compartment.oc1..aaaaaaaxxxxxxxxx"
region           = "ap-osaka-1"
image_tag        = "latest"
```

## デプロイ手順（クイックリファレンス）

```bash
# 1. イメージビルド & プッシュ
docker build -f docker/Dockerfile -t galley .
docker tag galley kix.ocir.io/{namespace}/galley:latest
docker push kix.ocir.io/{namespace}/galley:latest

# 2. Terraform apply
cd deploy/
terraform init
terraform apply

# 3. エンドポイント確認
terraform output mcp_endpoint_url
```

> OCIRプッシュ → Terraform apply の順序を守ること。逆だと古いイメージがデプロイされる。

## コンテナイメージ内の同梱ツール

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Terraform | 1.9.8 | IaCテンプレート実行 |
| kubectl | 1.30.7 | OKEクラスタ操作 |
| OCI CLI | 最新 (pip) | OCI API操作 |

## ネットワーク構成

| リソース | CIDR / ポート | 備考 |
|----------|--------------|------|
| VCN | `10.0.0.0/16` | |
| パブリックサブネット | `10.0.1.0/24` | API Gateway配置 |
| プライベートサブネット | `10.0.2.0/24` | Container Instance配置 |
| HTTPS (インバウンド) | `443` | パブリックサブネット |
| アプリケーション (内部) | `8000` | パブリック → プライベート |
