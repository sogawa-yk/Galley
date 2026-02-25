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

## フェーズ1: ヘルパー・テンプレート修正

- [x] `_sanitize_resource_name` staticメソッドを追加
  - [x] `re.sub(r'[^a-z0-9_]', '', name.replace(" ", "_").replace("-", "_").lower())` 実装
  - [x] 先頭が数字の場合 `_` をプレフィックスするロジック追加
  - [x] `_render_component_tf` の `safe_name` 生成を `_sanitize_resource_name` に置換
  - [x] `_build_local_references` の `safe_name` 生成を `_sanitize_resource_name` に置換

- [x] ADBテンプレートの `is_free_tier` をconfig反映に修正
  - [x] `_TF_RESOURCE_TEMPLATES["adb"]` の `is_free_tier = false` → `is_free_tier = {is_free_tier}` に変更
  - [x] `_TF_DEFAULTS["adb"]` に `"is_free_tier": "false"` を追加

- [x] Computeテンプレートをイメージdata source参照に変更
  - [x] `_TF_REQUIRED_DATA_SOURCES["compute"]` に `data "oci_core_images" "latest"` を追加
  - [x] Computeテンプレートの `source_id` を `data.oci_core_images.latest.images[0].id` に変更
  - [x] `_TF_REQUIRED_VARS["compute"]` から `image_id` エントリを削除

## フェーズ2: ローカル参照とサブネットテンプレート拡張

- [x] `_build_local_references` にネットワークリソースのマッピングを追加
  - [x] `internet_gateway` → `("var.gateway_id", "oci_core_internet_gateway")` を追加
  - [x] `route_table` → `("var.route_table_id", "oci_core_route_table")` を追加
  - [x] `security_list` → `("var.security_list_id", "oci_core_security_list")` を追加

- [x] subnetテンプレートに `route_table_id` と `security_list_ids` を追加
  - [x] `_TF_RESOURCE_TEMPLATES["subnet"]` にフィールド追加
  - [x] `_TF_REQUIRED_VARS["subnet"]` に `route_table_id` と `security_list_id` を追加

## フェーズ3: VCNネットワーク自動展開

- [x] `_expand_vcn_network` staticメソッドを実装
  - [x] VCNが存在し、subnetが存在しない場合 → パブリックサブネットを自動追加
  - [x] VCNが存在し、internet_gatewayが存在しない場合 → IGWを自動追加
  - [x] VCNが存在し、route_tableが存在しない場合 → ルートテーブルを自動追加
  - [x] VCNが存在し、security_listが存在しない場合 → セキュリティリストを自動追加
  - [x] VCNのdisplay_nameを基にした命名規則を適用

- [x] `export_iac` で `_expand_vcn_network` を呼び出し
  - [x] コンポーネントリストのローカルコピーを作成
  - [x] `_expand_vcn_network` を適用してからレンダリング

## フェーズ4: Mermaid可読性改善

- [x] `export_mermaid` のノードIDをdisplay_nameベースに変更
  - [x] `_sanitize_resource_name` を使用してノードIDを生成
  - [x] 接続エッジのsource_id/target_idもコンポーネントIDからdisplay_nameベースに変換

## フェーズ5: テスト追加・更新

- [x] `_sanitize_resource_name` のテスト
  - [x] 括弧を含む名前のテスト（`autonomous_db_(atp)` → `autonomous_db_atp`）
  - [x] 特殊文字（`@#$%`等）を含む名前のテスト
  - [x] 先頭数字のテスト（`123server` → `_123server`）
  - [x] 通常の名前のテスト（`My Server` → `my_server`）

- [x] VCNネットワーク自動展開のテスト
  - [x] VCN+Compute構成でsubnet/IGW/route_table/security_listが自動生成されるテスト
  - [x] ユーザーが明示的にsubnetを定義済みの場合はsubnetが自動生成されないテスト
  - [x] VCNなしの構成で自動展開が行われないテスト

- [x] ADB `is_free_tier` のテスト
  - [x] `config: {"is_free_tier": True}` → `is_free_tier = true` のテスト
  - [x] config未設定 → デフォルト `is_free_tier = false` のテスト

- [x] Computeイメージdata sourceのテスト
  - [x] main.tfに`data "oci_core_images"`が含まれるテスト
  - [x] variables.tfに`image_id`が含まれないテスト
  - [x] components.tfに`data.oci_core_images.latest.images[0].id`が含まれるテスト

- [x] Mermaid display_name IDのテスト
  - [x] ノードIDがdisplay_nameベースであるテスト
  - [x] UUIDがMermaid出力に含まれないテスト

- [x] 既存テストの更新
  - [x] `test_export_iac_compute_adds_dynamic_variables` の `image_id` アサーションを更新
  - [x] `test_export_iac_generates_tfvars_example` の `image_id` アサーションを更新
  - [x] ~~subnet関連テストの更新（route_table_id / security_list_id追加に対応）~~（既存テストは影響なし: VCN展開により自動的にローカル参照解決される）

## フェーズ6: 品質チェック

- [x] すべてのテストが通ることを確認
  - [x] `uv run pytest tests/ -x -q` → 243 passed
- [x] リントエラーがないことを確認
  - [x] `uv run ruff check src/ tests/` → All checks passed
- [x] フォーマットが適用されていることを確認
  - [x] `uv run ruff format --check src/ tests/` → 62 files already formatted
- [x] 型エラーがないことを確認
  - [x] `uv run mypy src/` → Success: no issues found

---

## 実装後の振り返り

### 実装完了日
2026-02-26

### 計画と実績の差分

**計画と異なった点**:
- 計画通り実装完了。大きな設計変更はなし
- `_sanitize_resource_name`に空文字列フォールバック(`"resource"`)を追加（検証サブエージェントの推奨による）
- `export_mermaid`の接続エッジフォールバックでも`_sanitize_resource_name`を使用するよう改善（検証サブエージェントの推奨による）

**新たに必要になったタスク**:
- なし（計画段階で正確にスコープ設定できていた）

### 学んだこと

**技術的な学び**:
- VCNネットワーク自動展開は`export_iac`内でのみ行い、元のアーキテクチャモデルを変更しない設計が重要。これにより`save_architecture`で保存された構成と`export_iac`の出力が独立する
- `_build_local_references`の参照マップ方式は、リソース間の依存関係を宣言的に表現でき、VCN関連リソースの追加が容易だった
- Terraform data sourceによるイメージ自動取得は、検証用途で非常に有用。RM経由の場合、image_idの手動設定が不要になる
- リソース名のサニタイズは正規表現1行で解決できるシンプルな修正だが、影響範囲が広い（`_render_component_tf`、`_build_local_references`、`export_mermaid`）ため、共通ヘルパーに切り出す設計が正解

**プロセス上の改善点**:
- フィードバックの6項目を分析し、実装可能なものとスコープ外を明確に分離できた
- 検証サブエージェントが防御コードの欠如（空文字列フォールバック）を検出し、品質向上に貢献

### 次回への改善提案
- ジョブ管理・ロック制御（フィードバック項目2）の改善は別タスクとして計画すべき
- VCN自動展開のルール（生成するリソースの種類・構成）は将来的にYAML定義に外出しすると拡張性が向上する
- `_expand_vcn_network`の生成順序はTerraform依存グラフに任せているが、`depends_on`の明示を検討してもよい
