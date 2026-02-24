# Galley MCP サーバー Terraform ワークフロー フィードバック

**日付:** 2026-02-24
**セッションID:** `c9368ea7-0a2a-44bb-8a38-a072f713a5c8`
**検証シナリオ:** 開発・検証用 Compute Instance + Autonomous Database (ATP) の構築

---

## 概要

ヒアリング → アーキテクチャ設計 → Terraform生成 → plan/apply のワークフローを検証した結果、主に Terraform 実行周りで複数の問題が確認されました。以下に問題点と改善提案をまとめます。

---

## 1. 【P0 ブロッカー】`terraform init` が実行できない

### 問題

`run_terraform_plan` / `run_terraform_apply` のどちらも、事前に `terraform init` が完了していることを前提としていますが、init を実行する手段が提供されていません。

- `run_oci_cli` は `terraform` コマンドを許可しない（`CommandNotAllowedError`）
- `run_terraform_plan` は内部で init を自動実行しない
- `.terraform.lock.hcl` を手動配置しても、provider プラグイン本体が存在しないため失敗

### エラーログ

```
Error: Inconsistent dependency lock file
  - provider registry.terraform.io/oracle/oci: required by this configuration but no version is selected
To make the initial dependency selections that will initialize the dependency lock file, run:
  terraform init
```

### 提案

- **案A（推奨）:** `run_terraform_plan` の内部で `terraform init -input=false` を自動実行する
- **案B:** `run_terraform_init` ツールを新規追加する

---

## 2. 【P1】ファイル配置パスが不明瞭

### 問題

`run_terraform_plan` の `terraform_dir` パラメータにどのパスを渡すべきかが分かりづらく、試行錯誤が必要でした。

| 試行 | パス | 結果 |
|------|------|------|
| 1 | `/home/claude/terraform` | `No such file or directory`（ツール側ファイルシステムが別） |
| 2 | `terraform`（相対パス） | `/app/terraform` に解決されて失敗 |
| 3 | `/data/sessions/{id}/app/terraform` | ファイルに到達（ただし init 未実行で失敗） |

### 提案

- `export_iac` のレスポンスに **`terraform_dir` のフルパス**を含める
- または `run_terraform_plan` が `session_id` からパスを自動解決する設計にする（`terraform_dir` パラメータを不要にする）

---

## 3. 【P1】`export_iac` がスケルトン（コメントアウト）のみ

### 問題

`export_iac` が返す `components.tf` は全リソースが TODO コメントになっており、そのままでは使用できません。

```hcl
# Dev Compute Instance (compute)
# TODO: Implement compute resource
# resource "oci_compute" "dev_compute_instance" {
#   shape = 'VM.Standard.E4.Flex'
# }
```

LLM が全リソースを正しい OCI Terraform 構文で書き直す必要があり、エラーが混入しやすくなります。

### 提案

サービスタイプごとに**実際に動作するリソース定義**を生成する。例：

- `compute` → `oci_core_instance` + `oci_core_vcn` + `oci_core_subnet` 等の依存リソース
- `adb` → `oci_database_autonomous_database`
- `vcn` → `oci_core_vcn` + `oci_core_internet_gateway` + `oci_core_route_table` + `oci_core_security_list`

VCN/Subnet/IGW/Route Table/Security List などの必須ネットワークリソースは自動的に含めるとよいです。

---

## 4. 【P2】ヒアリング完了 → アーキテクチャ保存の断絶

### 問題

`complete_hearing` 後に `export_iac` を呼ぶと `ArchitectureNotFoundError` が発生しました。ヒアリング完了からアーキテクチャ保存への自動連携がないため、LLM が `save_architecture` を明示的に呼ぶ必要があります。

### フロー上のギャップ

```
complete_hearing → (ギャップ) → save_architecture → export_iac
                   ^^^^^^^^^^^^^^
                   ここが暗黙的で、ドキュメントにも記載なし
```

### 提案

- `complete_hearing` のレスポンスに次のステップとして `save_architecture` を案内する
- または `complete_hearing` 時にヒアリング結果から推奨アーキテクチャを自動生成・保存するオプションを追加する

---

## 5. 【P2】plan 実行時の変数注入の仕組みがない

### 問題

`terraform plan` は必須変数が未設定だとエラーになります。検証（dry-run）目的で plan を回す際、ダミー値を注入する仕組みがありません。

```
Error: No value for required variable
  on variables.tf line 1:
   1: variable "region" {
```

### 提案

- `run_terraform_plan` に `variables` パラメータを追加し、key-value で変数を渡せるようにする
- またはセッションのヒアリング結果（例: region）から `terraform.tfvars` を自動生成する

---

## 優先度サマリー

| 優先度 | 項目 | 影響 |
|--------|------|------|
| **P0** | `terraform init` が実行できない | plan/apply が完全にブロックされる |
| **P1** | ファイル配置パスが不明瞭 | LLM の試行錯誤が増え、トークン浪費 |
| **P1** | `export_iac` がスケルトンのみ | LLM のコード生成エラーリスク増大 |
| **P2** | ヒアリング → アーキテクチャ保存の断絶 | ワークフローの分かりづらさ |
| **P2** | plan 時の変数注入の仕組み | dry-run 検証ができない |

---

## 補足: 正常に動作した部分

- ヒアリングフロー（`create_session` → `get_hearing_questions` → `save_answers_batch` → `complete_hearing`）は問題なく動作
- `save_architecture` によるアーキテクチャ保存は正常
- `export_summary` / `export_mermaid` による成果物出力は正常
- `scaffold_from_template` + `update_app_code` によるファイル配置は正常

---
## 対応結果
- **対応日**: 2026-02-24
- **ステアリング**: `.steering/20260224-terraform-workflow-feedback/`
- **対応内容の要約**: フィードバック5件（P0: terraform init自動実行、P1: terraform_dirパス返却、P1: export_iac実リソース生成、P2: complete_hearing→save_architecture案内、P2: Terraform変数注入）は全て実装済みであることを確認。追加で実装検証により発見された型安全性の問題（`_ensure_terraform_init`のパラメータ型、middleware/hearing.pyの型注釈）とlint違反（e2eテストの未使用import・行長超過）を修正。全195テストパス、ruff check/format/mypyクリア。
