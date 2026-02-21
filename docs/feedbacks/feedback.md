# Galley MCP Server デバッグフィードバックレポート

**セッションID:** `5fcaf1fc-52c7-49f4-83ae-8b3525d77341`
**日時:** 2026-02-19
**テストシナリオ:** OCI Functionsパフォーマンス検証環境のヒアリング → アーキテクチャ設計 → Terraform生成・実行

---

## 1. ヒアリングフェーズ（問題なし）

`create_session` → `get_hearing_questions` → `get_hearing_flow` → `save_answers_batch` → `complete_hearing` の一連のフローは正常に動作しました。特に問題はありません。

---

## 2. アーキテクチャ設計フェーズ（軽微な問題あり）

### 2.1 `export_iac` の前提条件エラーメッセージ

**問題:** ヒアリング完了後に `export_iac` を呼ぶと `ArchitectureNotFoundError` が返る。ヒアリング結果からアーキテクチャが自動生成されるわけではなく、`save_architecture` を明示的に呼ぶ必要があることがLLMには分からない。

**再現手順:**
1. `complete_hearing` でヒアリング完了
2. 直後に `export_iac` を呼ぶ

**期待される動作案:**
- `export_iac` のエラーメッセージに「先に `save_architecture` を実行してください」等のガイダンスを含める
- または `complete_hearing` のレスポンスに「次のステップ: `save_architecture` でアーキテクチャを保存してください」を含める

### 2.2 `save_architecture` の `connections` における ID 指定の曖昧さ

**問題:** `save_architecture` の `connections` パラメータで `source_id` / `target_id` に何を指定すべきか不明確。`save_architecture` は **コンポーネントをこれから作成する** APIなので、呼び出し時点ではコンポーネントIDが存在しない。LLMは便宜的に `"apigateway-1"`, `"functions-1"` のような仮IDを使ったが、レスポンスで返された実際のIDは UUID だった。

**実際の挙動:**
- リクエスト: `source_id: "apigateway-1"`, `target_id: "functions-1"`
- レスポンスのコンポーネントID: `3cf38cf2-...`, `7e73f4b3-...`, `a4b0d4f1-...`
- connections はリクエストで渡した仮IDがそのまま保存された

**提案:**
- connections で components 配列のインデックスを参照する方式にする（例: `source_index: 2, target_index: 1`）
- または components と connections を別々のAPI呼び出しにし、`add_component` の戻り値IDを `connections` で使う
- あるいは、レスポンス時に仮IDを実際のUUIDにマッピングし直す

---

## 3. Terraformテンプレート生成フェーズ（要改善）

### 3.1 `export_iac` の出力がスケルトンのみ

**問題:** `export_iac` が返すTerraformコードは `# TODO: Implement` のコメント付きスケルトンのみ。実際に動作するリソース定義は含まれておらず、LLMが全てのTerraformコードをゼロから書く必要がある。

**返されたcomponents.tf:**
```hcl
# Test VCN (vcn)
# TODO: Implement vcn resource
# resource "oci_vcn" "test_vcn" {
#   cidr_block = '10.0.0.0/16'
# }
```

**影響:**
- LLMが正確なOCI Terraform Providerのリソース名・属性を全て知っている前提になる
- ネットワーク周辺リソース（サブネット、ルートテーブル、セキュリティリスト、ゲートウェイ等）は `save_architecture` のコンポーネントに含まれていなくても必要だが、テンプレートには含まれない
- OCI Functions には Application → Function の2階層が必要だが、テンプレートのスケルトンは `oci_functions` という存在しないリソース名を示唆している（正しくは `oci_functions_application` + `oci_functions_function`）

**提案:**
- サービスタイプごとに、動作するTerraformリソース定義のテンプレートを内蔵する
- 暗黙的に必要なリソース（VCN→サブネット、Functions→Application等）も自動的に含める
- 少なくともリソース名は正確なOCI Provider名にする

### 3.2 テンプレートのシンタックスエラー

**問題:** スケルトン内のコメントに `'10.0.0.0/16'`（シングルクォート）が使われている。HCLではダブルクォートが正しい。LLMがこれをそのまま使うとシンタックスエラーになる。

---

## 4. Terraform実行フェーズ（重大な問題あり）

### 4.1 `run_terraform_plan` のファイルパス解決 — 最も深刻な問題

**問題:** MCP server（Python FastMCPプロセス）のファイルシステムとLLMツール環境（Dockerコンテナ）のファイルシステムが分離されており、LLM側で作成したファイルをMCP server側の `run_terraform_plan` で参照できない。

**再現手順と試行錯誤の詳細:**

| 試行 | `terraform_dir` の値 | MCPが解決したパス | 結果 |
|------|----------------------|-------------------|------|
| 1 | `/home/claude/terraform` | `/home/claude/terraform` | `[Errno 2] No such file or directory` |
| 2 | `terraform` | `/app/terraform` | `[Errno 2] No such file or directory` |
| 3 | `/app/terraform` | `/app/terraform` | `[Errno 2] No such file or directory` |
| 4 | `/tmp/terraform` | `/tmp/terraform` | `[Errno 2] No such file or directory` |

**補足:** 試行2から、MCP serverが相対パスを `/app/` をベースとして解決していることが判明（`terraform` → `/app/terraform`）。しかし `/app/terraform` は MCP server のコンテナ/プロセス内には存在しない。

**根本原因:** `export_iac` で返されるTerraformコードはJSON文字列としてレスポンスに含まれるだけで、MCP server側のファイルシステムには書き込まれない。一方 `run_terraform_plan` はMCP server側のファイルシステム上の実ファイルを期待する。この2つのツールの間にファイルを橋渡しするメカニズムがない。

**回避策として試みたこと:**
1. `scaffold_from_template` で `rest-api-adb` テンプレートをスキャフォールドし、`/data/sessions/{session_id}/app/` にファイルを生成
2. `update_app_code` で `terraform/main.tf`, `terraform/variables.tf`, `terraform/components.tf` をサーバー側に作成
3. `run_terraform_plan` に `/data/sessions/{session_id}/app/terraform` を指定 → **成功（パスは解決された）**

**提案（優先度高）:**
- **案A:** `export_iac` 実行時にMCP server側のファイルシステムにもTerraformファイルを自動的に書き出し、書き出し先パスをレスポンスに含める。`run_terraform_plan` はそのパスをそのまま受け取れるようにする
- **案B:** `run_terraform_plan` にTerraformコードをインラインで渡せるパラメータを追加する（一時ディレクトリに書き出して実行）
- **案C:** `write_terraform_files(session_id, files: dict)` のような専用ツールを追加し、`export_iac` → `write_terraform_files` → `run_terraform_plan` のフローにする

### 4.2 `terraform init` が実行されない

**問題:** `run_terraform_plan` の前に `terraform init` が必要だが、Galleyにはinitを実行するツールがない。

**エラーメッセージ:**
```
Error: Inconsistent dependency lock file
  - provider registry.terraform.io/oracle/oci: required by this configuration but no version is selected
To make the initial dependency selections that will initialize the dependency lock file, run:
  terraform init
```

**提案:**
- `run_terraform_plan` 内部で自動的に `terraform init` を実行する（init未実行を検知した場合）
- または `run_terraform_init` ツールを追加する
- **推奨:** planの前に自動initが最もシンプルで、LLM側のツール呼び出し回数を減らせる

### 4.3 Terraform変数の渡し方

**問題:** `run_terraform_plan` に変数値（`-var` や `-var-file`）を渡す手段がない。検証環境でもregion/compartment_id/tenancy_ocidは必須。

**回避策:** variables.tf に `default` 値を設定したが、実運用では不適切（OCIDがハードコードされる）。

**提案:**
- `run_terraform_plan` に `variables: dict` パラメータを追加し、内部で `-var key=value` に変換する
- またはセッションに紐づくOCI設定（region, compartment_id等）を保持し、自動的にtfvarsとして渡す
- ヒアリング時に取得したOCI接続情報をTerraform実行時に自動注入する仕組み

### 4.4 `run_oci_cli` でのTerraformコマンド実行

**問題:** 最後の手段として `run_oci_cli` で `cd ... && terraform init` を試みたが、`run_oci_cli` は「許可されたサービスコマンドのみ実行可能」とドキュメントにあり、任意のシェルコマンドは実行不可と推測される。

**提案:** これは意図通りの制限だと思われるが、上記4.2のinit問題が解決されれば不要。

---

## 5. テンプレートシステムの制約

### 5.1 OCI Functions用テンプレートの不在

**問題:** `list_templates` で返されるテンプレートは `rest-api-adb` の1つのみ。OCI Functionsの検証が目的なのにFunctions用テンプレートがなく、無関係な `rest-api-adb` をスキャフォールドしてファイルパスを確保する必要があった。

**提案:**
- サーバーレス（Functions + API Gateway）テンプレートの追加
- 最低限、空のプロジェクトを作れる「blank」テンプレートの追加
- テンプレート不要でもTerraformファイルを配置できるメカニズム（上記4.1の提案参照）

### 5.2 `update_app_code` の前提条件

**問題:** `update_app_code` は `scaffold_from_template` 済みでないと `AppNotScaffoldedError` になる。Terraformファイルを直接サーバーに配置する手段がこのツール経由しかないため、無関係なテンプレートをスキャフォールドせざるを得なかった。

---

## 6. ワークフロー全体の設計に関する提案

### 6.1 理想的なワークフロー（提案）

```
create_session
    ↓
get_hearing_questions + get_hearing_flow
    ↓
save_answers_batch (対話的に回答収集)
    ↓
complete_hearing
    ↓
save_architecture (ヒアリング結果からアーキテクチャ設計)
    ↓
generate_terraform (★新規: 動作するTerraformコードを自動生成しサーバー側に配置)
    ↓                   戻り値: terraform_dir パス
run_terraform_plan (★自動init付き、変数は自動注入)
    ↓
[エラー時] LLMがコード修正 → update_terraform_file → re-plan ループ
    ↓
run_terraform_apply
```

### 6.2 現状のボトルネックまとめ

| 問題 | 影響度 | 修正難易度 |
|------|--------|-----------|
| export_iac → run_terraform_plan のファイル橋渡し不在 | 🔴 致命的 | 中 |
| terraform init 自動実行なし | 🔴 致命的 | 低 |
| Terraform変数の渡し方がない | 🟡 高 | 低 |
| export_iac のスケルトンが不完全 | 🟡 高 | 中〜高 |
| Functions用テンプレートなし | 🟡 中 | 中 |
| save_architecture の connection ID 問題 | 🟢 低 | 低 |
| export_iac スケルトンのシンタックス（シングルクォート） | 🟢 低 | 低 |

---

## 7. 正常に動作した部分（ポジティブフィードバック）

- **ヒアリングフロー全体** — `create_session` → `complete_hearing` までスムーズ
- **`save_answers_batch`** — 複数回答の一括保存が便利
- **`list_available_services`** — 利用可能サービス一覧のconfig_schemaがLLMのアーキテクチャ設計に非常に有用
- **`save_architecture`** — コンポーネントの保存自体は正常動作
- **`update_app_code`** — scaffold済みであればファイル配置が機能する（スナップショット付きで安全）
- **`run_terraform_plan` のエラー出力** — stderrが正確に返されるため、LLMによるデバッグループは機能する（パス問題さえ解決すれば）
- **エラーメッセージの質** — 全体的にエラーメッセージが明確で、LLMが原因特定しやすい

---
## 対応結果
- **対応日**: 2026-02-19
- **ステアリング**: `.steering/20260219-feedback-fix/`
- **対応内容の要約**: フィードバックの優先度「致命的」〜「低」の全7問題に対応。`ArchitectureNotFoundError`のガイダンス追加、`complete_hearing`レスポンスの`next_step`追加、`save_architecture`の仮ID→UUID自動解決、`export_iac`のTerraformテンプレート実装（10サービスタイプ対応）・ファイル書き出し・`terraform_dir`返却、`terraform init`自動実行、`variables`パラメータ追加。全190テストパス。
