# 設計書

## アーキテクチャ概要

既存の`DesignService.export_iac()`を拡張し、コンポーネントのサービスタイプに応じた動的変数生成を追加。その上でE2Eテスト層を新設し、生成されたTerraformコードを実際のterraformコマンドで検証する。

```
テストピラミッド:

  Unit Tests (195件)         ← モック使用、高速
  Integration Tests          ← FastMCP Client経由
  E2E: validate (12件)       ← 実terraform、OCI不要
  E2E: plan (3件)            ← 実terraform + OCI API
  E2E: lifecycle (1件)       ← 実リソース作成・削除
```

## コンポーネント設計

### 1. 動的変数生成 (`src/galley/services/design.py`)

**責務**:
- サービスタイプごとに必要なTerraform変数を定義するマッピング管理
- `export_iac()`実行時にコンポーネントを走査し、必要な変数・data sourceを動的追加

**実装の要点**:
- `_TF_REQUIRED_VARS`: サービスタイプ → 必要な変数定義リストのマッピング
  - compute → `image_id`, `subnet_id`
  - oke → `vcn_id`, `subnet_id`
  - apigateway → `subnet_id`
  - functions → `subnet_id`, `function_image`
  - loadbalancer → `subnet_id`
  - objectstorage → `object_storage_namespace`
- `_TF_REQUIRED_DATA_SOURCES`: サービスタイプ → data sourceブロックのマッピング
  - compute → `oci_identity_availability_domains`
- 同一変数名の重複排除（`seen_vars: set[str]`）
- data sourceブロックは`main.tf`末尾に追加

### 2. E2Eテストインフラ (`tests/e2e/conftest.py`)

**責務**:
- E2E専用フィクスチャの提供
- OCI接続情報の環境変数からの取得

**実装の要点**:
- `oci_compartment_id` / `oci_region`: 環境変数 `GALLEY_TEST_COMPARTMENT_ID` / `GALLEY_TEST_REGION` から取得（デフォルト: `docs/environment.md`の値）
- `terraform_variables`: `{"compartment_id": ..., "region": ...}` のdict
- `create_session_with_component()`: session作成→hearing完了→architecture保存→export_iac を一括実行

### 3. terraform validateテスト (`tests/e2e/test_terraform_validate.py`)

**責務**:
- 生成されたTerraformコードの構文的正しさを検証

**実装の要点**:
- `_run_subprocess()`で`terraform init -backend=false` → `terraform validate`を実行
- 10サービスタイプをパラメトリックにテスト
- 複数コンポーネント組み合わせテスト
- 全10サービスタイプ同時テスト
- OCI不要、約25秒

### 4. terraform planテスト (`tests/e2e/test_terraform_plan.py`)

**責務**:
- 生成されたTerraformコードが実OCI環境でplanを生成できることを検証

**実装の要点**:
- `infra_service.run_terraform_plan()`をモックなしで実行
- VCN / ADB で`result.success`, `result.plan_summary`を検証
- auto-init動作の実環境検証
- OCI接続必要、約9秒

### 5. terraform lifecycleテスト (`tests/e2e/test_terraform_lifecycle.py`)

**責務**:
- VCNのフルライフサイクル（plan→apply→re-plan→destroy）を検証

**実装の要点**:
- テスト用CIDR `10.254.0.0/16`で既存リソースと衝突回避
- `try/finally`でdestroy保証（テスト失敗時もクリーンアップ）
- re-planで冪等性確認（"No changes"）
- `@pytest.mark.e2e_lifecycle`マーカー
- OCI接続必要、約60-120秒

## データフロー

### E2Eテスト実行フロー
```
1. create_session_with_component()でセッション作成→hearing完了→architecture保存→export_iac
2. 生成されたterraform_dirに対してterraformコマンドを実行
3. validate: terraform init -backend=false → terraform validate
4. plan: infra_service.run_terraform_plan() (auto-init含む)
5. lifecycle: plan → apply → re-plan → destroy (try/finallyでcleanup保証)
```

## エラーハンドリング戦略

### lifecycleテストのクリーンアップ
- `try/finally`パターンでapply成功後のdestroy実行を保証
- テスト失敗時（assert failure）でもfinallyブロックでdestroy実行

### OCI quota超過
- lifecycleテストはOCI環境のquota制約を受ける
- テスト自体は正しく構造化されており、quota内であれば成功する

## テスト戦略

### ユニットテスト（既存 + 追加）
- 動的変数生成: compute → `image_id`, `subnet_id`変数追加を検証
- data source追加: compute → `oci_identity_availability_domains`を検証
- 変数重複排除: oke + apigateway → `subnet_id`が1回だけ宣言
- 追加変数なし: VCNのみ → 余計な変数が生成されない
- objectstorage → `object_storage_namespace`変数追加を検証

### E2Eテスト
- validate: 全10サービスタイプの構文検証
- plan: VCN/ADBの実OCI plan
- lifecycle: VCNのフルサイクル（plan/apply/re-plan/destroy）

## 依存ライブラリ

新しいライブラリの追加なし。既存の依存のみ使用:
- `pytest` (markers, parametrize)
- `asyncio` (subprocess実行)

## ディレクトリ構造

```
src/galley/services/design.py        # _TF_REQUIRED_VARS, _TF_REQUIRED_DATA_SOURCES 追加
tests/unit/services/test_design.py   # 動的変数生成テスト追加
tests/e2e/
├── __init__.py                      # 新規（空）
├── conftest.py                      # E2E専用フィクスチャ
├── test_terraform_validate.py       # terraform validate（OCI不要）
├── test_terraform_plan.py           # terraform plan（OCI API接続）
└── test_terraform_lifecycle.py      # terraform apply + destroy（実リソース）
pyproject.toml                       # markers, addopts 追加
```

## 実装の順序

1. `export_iac`の`variables.tf`動的生成を修正（design.py）
2. 既存ユニットテスト更新・追加（test_design.py）
3. 既存テスト回帰なし確認
4. pyproject.tomlにマーカーと`addopts`を追加
5. `tests/e2e/`ディレクトリとconftest.pyを作成
6. `test_terraform_validate.py`を実装・実行
7. `test_terraform_plan.py`を実装・実行
8. `test_terraform_lifecycle.py`を実装・実行

## セキュリティ考慮事項

- E2Eテストのデフォルトcompartment IDはdocs/environment.mdから取得
- 環境変数`GALLEY_TEST_COMPARTMENT_ID`でオーバーライド可能
- lifecycleテストは実リソース作成のためquota消費に注意

## パフォーマンス考慮事項

- validateテスト: 各テストでterraform init（OCI providerダウンロード）が発生するため、初回は数十秒かかる
- 2回目以降はproviderキャッシュにより高速化
- `--ignore=tests/e2e`でデフォルトのpytest実行には影響なし

## 将来の拡張性

- 新しいサービスタイプ追加時は`_TF_REQUIRED_VARS`と`_TF_REQUIRED_DATA_SOURCES`にエントリを追加するだけ
- CI/CDパイプラインへのE2Eテスト統合（validate のみをCIに含める等）
