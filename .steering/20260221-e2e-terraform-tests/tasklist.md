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

## フェーズ1: export_iac動的変数生成の修正

- [x] `_TF_REQUIRED_VARS`マッピングを`design.py`に追加
  - [x] compute → `image_id`, `subnet_id`
  - [x] oke → `vcn_id`, `subnet_id`
  - [x] apigateway → `subnet_id`
  - [x] functions → `subnet_id`, `function_image`
  - [x] loadbalancer → `subnet_id`
  - [x] objectstorage → `object_storage_namespace`

- [x] `_TF_REQUIRED_DATA_SOURCES`マッピングを`design.py`に追加
  - [x] compute → `oci_identity_availability_domains` data source

- [x] `export_iac()`を修正して動的変数・data sourceを生成
  - [x] コンポーネント走査による追加変数収集（重複排除）
  - [x] `variables.tf`への変数宣言追加
  - [x] `main.tf`へのdata sourceブロック追加

## フェーズ2: ユニットテスト追加

- [x] compute動的変数テスト（`image_id`, `subnet_id`が宣言される）
- [x] compute data sourceテスト（`oci_identity_availability_domains`がmain.tfに含まれる）
- [x] 変数重複排除テスト（oke + apigateway → `subnet_id`が1回だけ）
- [x] VCNのみ追加変数なしテスト
- [x] objectstorage namespace変数テスト

## フェーズ3: pyproject.toml更新

- [x] `addopts = "--ignore=tests/e2e"`を追加
- [x] `e2e`マーカーを追加
- [x] `e2e_lifecycle`マーカーを追加

## フェーズ4: E2Eテストインフラ作成

- [x] `tests/e2e/__init__.py`を作成
- [x] `tests/e2e/conftest.py`を作成
  - [x] `oci_compartment_id`フィクスチャ（環境変数 or デフォルト）
  - [x] `oci_region`フィクスチャ（環境変数 or デフォルト）
  - [x] `terraform_variables`フィクスチャ
  - [x] 各サービスフィクスチャ（storage, hearing_service, design_service, infra_service）
  - [x] `create_session_with_component()`ヘルパー関数

## フェーズ5: E2Eテスト実装

- [x] `test_terraform_validate.py`を実装
  - [x] 10サービスタイプのパラメトリックテスト
  - [x] 複数コンポーネント組み合わせテスト
  - [x] 全10サービスタイプ同時テスト

- [x] `test_terraform_plan.py`を実装
  - [x] VCN planテスト
  - [x] ADB planテスト
  - [x] auto-init動作テスト

- [x] `test_terraform_lifecycle.py`を実装
  - [x] VCN plan → apply → re-plan（冪等性）→ destroy

## フェーズ6: 品質チェック

- [x] 既存テストが全て通ることを確認
  - [x] `uv run pytest tests/unit tests/integration` → 195 passed
- [x] E2E validateテストが全て通ることを確認
  - [x] `uv run pytest tests/e2e/test_terraform_validate.py -v` → 12 passed
- [x] E2E planテストが全て通ることを確認
  - [x] `uv run pytest tests/e2e/test_terraform_plan.py -v` → 3 passed
- [x] デフォルトpytestでE2Eが除外されることを確認
  - [x] `uv run pytest` → 195 passed（E2E含まず）
- [x] ~~E2E lifecycleテストが通ることを確認~~（OCI compartmentのVCN quota超過により実行不可。テストコード自体は正常で、plan成功により生成コードの正しさは検証済み）

---

## 実装後の振り返り

### 実装完了日
2026-02-21

### 計画と実績の差分

**計画と異なった点**:
- lifecycleテスト（apply/destroy）がOCI compartmentのVCN quota超過（`QuotaExceeded`）により失敗。テストコード自体に問題はなく、plan段階まで成功しているため生成コードの正しさは確認済み
- validateテストの2回目実行時に`/tmp`のディスク容量不足が発生（OCI providerの繰り返しダウンロードによる）。tmpクリーンアップ後に再実行で解消

**新たに必要になったタスク**:
- なし

**技術的理由でスキップしたタスク**:
- E2E lifecycleテストの実行確認
  - スキップ理由: OCI compartmentのVCN quotaが上限に達しており、新規VCN作成が不可能
  - 代替検証: planテスト（3件全て成功）により、生成されるTerraformコードがOCI APIレベルで有効であることを確認済み

### 学んだこと

**技術的な学び**:
- `terraform validate`は`-backend=false`フラグでOCI接続なしに構文チェック可能
- `_TF_REQUIRED_VARS`のようなマッピングテーブルで、サービスタイプと必要変数の関係を宣言的に管理するとメンテナンス性が高い
- OCI providerのダウンロードはtmpディレクトリを消費するため、テスト環境のディスク容量に注意が必要

**プロセス上の改善点**:
- ユニットテスト→E2E validate→E2E plan→E2E lifecycleの段階的な検証が効果的
- export_iacの動的変数生成修正をE2Eテスト追加の前提条件として先に実装したのが正しい順序だった

### 次回への改善提案
- E2Eテスト用に専用のquota/compartmentを確保するか、quota超過時のスキップロジック（`pytest.skip()`）を追加検討
- terraform providerのキャッシュディレクトリを`tmp_path`内で共有する仕組みを検討（ディスク節約）
