# Business Logic Model - Unit 5: App Deployment

## Overview

App Deployment Skillは3段階のフローで動作する：
1. **ビルド**: コンテナイメージのビルド
2. **プッシュ**: OCIRへのイメージプッシュ
3. **デプロイ**: compute_typeに応じたデプロイ実行

## フロー詳細

```
generated/{project-name}/app/      (Unit 4の出力)
generated/{project-name}/stack_outputs.json  (Unit 3の出力)
      |
      v
[Phase 1: ビルド]
      | docker build
      | -> {project-name}:latest
      v
[Phase 2: OCIRプッシュ]
      | docker tag + docker push
      | -> {region}.ocir.io/{namespace}/{project-name}:latest
      v
[Phase 3: デプロイ]  <--+
      | compute_typeに応じて:          |
      | - OKE: kubectl apply           |
      | - CI: oci container-instances  |
      | - Compute: docker run (SSH)    |
      | - Functions: fn deploy         |
      | 失敗時 -> 修正+再試行 ---------+ (最大2回)
      v
[Phase 4: 結果出力]
      | endpoints.json 生成
      v
Complete
```

## Phase 1: ビルド

- `generated/{project_name}/app/Dockerfile` を使用
- イメージ名: `{project_name}:latest`
- ビルドコンテキスト: `generated/{project_name}/app/`

## Phase 2: OCIRプッシュ

- stack_outputs.jsonからリージョン、テナンシー情報を取得
- OCIRログイン → タグ → プッシュ
- OCIR URL: `{region}.ocir.io/{tenancy_namespace}/{project_name}:latest`

## Phase 3: デプロイ

compute_typeに応じてデプロイ方式を切り替え:

| compute_type | Deploy Method | Key Info from stack_outputs |
|---|---|---|
| oke | kubectl apply (manifests生成) | oke_cluster_id, oke_kubeconfig |
| container_instances | OCI CLI で既存CIを更新 or 新規CI作成 | container_instance_id, subnet_id |
| compute | SSH + docker run | compute_public_ip |
| functions | fn deploy | functions_app_id |

### 自己修正ループ
- デプロイ失敗時: エラー分析 → 設定修正 → 再デプロイ（最大2回）

## Phase 4: 結果出力

- `generated/{project_name}/endpoints.json` を生成
- エンドポイントURL（後続のverify Skillが使用）
