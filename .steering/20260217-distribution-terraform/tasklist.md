# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### 実装可能なタスクのみを計画
- 計画段階で「実装可能なタスク」のみをリストアップ
- 「将来やるかもしれないタスク」は含めない
- 「検討中のタスク」は含めない

### タスクスキップが許可される唯一のケース
以下の技術的理由に該当する場合のみスキップ可能:
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

### タスクが大きすぎる場合
- タスクを小さなサブタスクに分割
- 分割したサブタスクをこのファイルに追加
- サブタスクを1つずつ完了させる

---

## フェーズ1: Dockerfile作成

- [x] `docker/Dockerfile`を作成する（マルチステージビルド）
  - [x] ステージ1（builder）: Python依存関係のインストールとパッケージビルド
  - [x] ステージ2（runtime）: OCI CLI、Terraform、kubectlのインストール
  - [x] アプリケーションの配置、非rootユーザー設定、ヘルスチェック、エントリポイント

## フェーズ2: 配布用Terraform作成

- [x] `deploy/main.tf`を作成する（プロバイダー設定、Terraformバージョン制約）
- [x] `deploy/variables.tf`を作成する（入力変数定義、バリデーション）
- [x] `deploy/network.tf`を作成する（VCN、サブネット、ゲートウェイ、セキュリティリスト）
- [x] `deploy/object-storage.tf`を作成する（バケット作成、バージョニング）
- [x] `deploy/iam.tf`を作成する（Dynamic Group、IAM Policy）
- [x] `deploy/container-instance.tf`を作成する（Container Instance定義）
- [x] `deploy/api-gateway.tf`を作成する（API Gateway、Deployment、URLトークン認証）
- [x] `deploy/outputs.tf`を作成する（エンドポイントURL、URLトークン等の出力）

## フェーズ3: 設定ファイル更新と検証

- [x] `.gitignore`にTerraform関連の除外パターンを追加する
- [x] `terraform init && terraform validate`でTerraformの構文検証を行う
- [x] 既存テストの回帰確認（`uv run pytest`）
- [x] リントエラーがないことを確認（`uv run ruff check .`）
- [x] 型エラーがないことを確認（`uv run mypy src/`）

---

## 実装後の振り返り

### 実装完了日
2026-02-17

### 計画と実績の差分

**計画と異なった点**:
- OCI API GatewayのTOKEN_AUTHENTICATION認証ブロックのTerraform Provider スキーマがドキュメント通りに動作しなかった。`validation_policy.keys` の `type` 属性がサポートされておらず、`terraform validate` でエラーとなった。API Gatewayの認証は「クエリパラメータ存在チェック（API Gateway側）+ トークン値一致検証（アプリケーション側）」の2段構成に変更した。
- PRDのF3受け入れ条件では入力変数は4つ（`compartment_id`, `region`, `galley_work_compartment_id`, `image_tag`）だが、当初は`tenancy_id`を追加していた。その後、利用想定ユーザーにテナンシーレベルの権限がないことが判明し、`tenancy_id`を削除して`dynamic_group_id`（既存の動的グループOCID）に変更。動的グループの作成をTerraformから削除し、IAM PolicyはOCID参照（`dynamic-group id <ocid>`構文）でコンパートメントレベルに作成する方式に変更した。
- devcontainer環境がaarch64（ARM64）であり、最初にダウンロードしたamd64版Terraformバイナリが動作しなかった。arm64版に切り替えて検証を完了。
- `galley_work_compartment_id`のデフォルト値を`""`から`null`に変更。`coalesce()`が空文字列をnon-nullとして扱い、`compartment_id`へのフォールバックが機能しない問題をimplementation-validatorが検出。
- Container Instanceの環境変数に`GALLEY_BUCKET_NAME`, `GALLEY_BUCKET_NAMESPACE`, `GALLEY_REGION`, `GALLEY_URL_TOKEN`の4変数を追加。当初の計画には含まれていなかったが、Object Storage接続とURLトークン検証に必要。
- pytest-asyncioが開発環境にインストールされておらず、既存テストが全て失敗した。`uv add --dev pytest-asyncio`で解決。同様にruff、mypy等も未インストールだったため追加。

**新たに必要になったタスク**:
- `.dockerignore`の作成: ビルドコンテキストからTerraformファイルやテスト等を除外するため
- implementation-validatorの指摘に基づく5件の修正（環境変数追加、変数デフォルト値修正、セキュリティリストのCIDR参照化、OCIRリージョン対応、uvバージョンピン）

**技術的理由でスキップしたタスク**: なし

### 学んだこと

**技術的な学び**:
- OCI API GatewayのTerraform Providerは、TOKEN_AUTHENTICATIONのSTATIC_KEYS検証ポリシーがJWKS/JWT形式の鍵を前提としており、単純な文字列トークンの一致検証には使えない。シンプルなURLトークン認証にはアプリケーション側での検証が必要。
- Terraformの`coalesce()`関数は空文字列`""`をnon-nullとして扱うため、オプショナル変数のデフォルト値には`null`を使うべき。
- OCI Container Instanceへの環境変数渡しは、Object Storageバケット名やリージョンなどのTerraformで作成したリソース情報を伝達する重要な手段。設計時にContainer Instanceが必要とするすべての環境変数を洗い出すべき。
- devcontainer環境のアーキテクチャ（aarch64 vs amd64）を確認してからツールバイナリをダウンロードすること。

- OCI動的グループはテナンシーレベルのリソースであり、作成にはテナンシー管理者権限が必要。利用想定ユーザーにその権限がない場合は、既存の動的グループOCIDを入力変数として受け取る設計が適切。IAM Policyでは`dynamic-group id <ocid>`構文でOCIDを直接参照でき、名前解決のためのデータソースが不要。
- OCI Terraform Providerには`data "oci_identity_dynamic_group"`（単数）のデータソースが存在しない。`data "oci_identity_dynamic_groups"`（複数）はテナンシーOCIDが必要なため、テナンシー権限なしでは使えない。

**プロセス上の改善点**:
- implementation-validatorサブエージェントによる検証が非常に効果的だった。特にTerraformの`coalesce()`問題、環境変数の不足、セキュリティリストのハードコード問題など、手動では見落としやすい問題を検出できた。
- Terraform validateによる構文検証を実装フェーズの最後に配置したことで、全ファイル作成後にまとめて検証→修正できた。

### 次回への改善提案
- Container Instanceの環境変数は、設計段階で「アプリケーションが必要とするすべての設定」を洗い出し、variables.tf → container-instance.tf → アプリケーションの設定クラスの3つの整合性を確認する。
- OCI API Gatewayの認証方式は、Terraform Provider の実際のスキーマを事前に確認してから設計に反映する。ドキュメントとProviderの間に差異がある場合がある。
- URLトークンのアプリケーション側検証ロジックは、次のフェーズ（Phase 3以降）で実装が必要。`GALLEY_URL_TOKEN`環境変数との一致検証ミドルウェアを追加すること。
- PRDのF3受け入れ条件に`dynamic_group_id`変数の追加を反映する更新が必要。
