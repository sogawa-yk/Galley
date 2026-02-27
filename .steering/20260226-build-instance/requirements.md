# 要求仕様: ビルドインスタンスの追加

## 背景

- Galley本体はOCI Container Instanceで稼働しており、Docker daemonが利用できない
- 現在の`build_and_deploy`は`image_uri`（ビルド済みイメージ）を要求し、ユーザーが事前にビルド・プッシュする必要がある
- エンドツーエンドの自動化のため、ビルド用Compute Instanceを追加する

## 要求

### R1: Terraform構成にビルドインスタンスを追加
- `deploy/`にCompute Instanceリソースを追加
- cloud-initでDocker Engine + OCI CLIをインストール
- プライベートサブネットに配置（NAT GW経由で外部通信可能）

### R2: AppServiceにビルド機能を追加
- `_build_and_push_image`メソッドを実装
- Build Instance上でdocker build/pushをリモート実行
- ビルド結果（image_uri）を取得して後続のデプロイ処理に渡す

### R3: build_and_deployフローの拡張
- `image_uri`パラメータをオプション化
- `image_uri`未指定の場合: Build Instance → Docker build → OCIR push → kubectl apply
- `image_uri`指定の場合: 既存フロー（kubectl apply直行）

### R4: ツール層のパラメータ更新
- `build_and_deploy`ツールの`image_uri`をオプショナルに変更
- `build_instance_id`パラメータを追加（ビルド実行先）

### R5: テスト
- ビルドフローのユニットテスト（subprocess mock）
- 既存のデプロイテストが引き続きパスすること

## スコープ外
- Kaniko方式（将来候補として`docs/architecture.md`に記載済み）
- CI/CDパイプラインとの統合
