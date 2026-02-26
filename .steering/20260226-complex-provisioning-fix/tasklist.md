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

## フェーズ1: テンプレート修正とサニタイズ

- [x] nosqlテンプレートの`name`と`ddl_statement`を`{safe_name}`に変更
- [x] objectstorageテンプレートの`name`を`{safe_name}`に変更
- [x] streamingテンプレートの`name`を`{safe_name}`に変更
- [x] `_render_component_tf()`で`params["safe_name"]`を設定
- [x] API Gatewayの`endpoint_type`を`_render_component_tf()`で大文字化

## フェーズ2: ネットワーク参照ロジック修正

- [x] `_expand_vcn_network()`にNAT Gateway自動生成を追加
- [x] `_build_local_references()`でpublic/privateサブネットを区別
- [x] `_build_local_references()`でpublic/privateルートテーブルを区別
- [x] `_build_local_references()`でpublic/privateセキュリティリストを区別
- [x] `_build_local_references()`でIGWとNAT GWを区別
- [x] route_tableテンプレートのゲートウェイ参照をpublic/privateで切り替え
- [x] subnetテンプレートのroute_table/security_list参照をpublic/privateで切り替え
- [x] `export_iac()`のローカル参照置換でコンポーネント特性に基づく振り分け

## フェーズ3: リソーステンプレート追加・改善

- [x] OKEテンプレートにNode Poolリソースブロックを追加
- [x] `_TF_DEFAULTS["oke"]`にNode Pool関連デフォルト値を追加
- [x] ADBテンプレートにプライベートエンドポイント用ブロックを追加
- [x] `_TF_REQUIRED_VARS["adb"]`にsubnet_id条件付き追加

## フェーズ4: バリデーション強化

- [x] `ArchitectureValidator`にコンポーネント名の命名規則チェックを追加
- [x] `ArchitectureValidator`にpublicリソースのサブネット配置整合性チェックを追加

## フェーズ5: テスト

- [x] nosql/objectstorage/streaming名サニタイズのテスト追加
- [x] API Gateway endpoint_type大文字化のテスト追加
- [x] 複数サブネット構成のローカル参照テスト追加
- [x] OKE Node Pool生成のテスト追加
- [x] ADBプライベートエンドポイントのテスト追加
- [x] バリデーション（命名規則/サブネット配置）のテスト追加
- [x] 既存テストが全てパスすることを確認（258/258 passed）

## フェーズ6: 品質チェック

- [x] `uv run ruff check src/ tests/` エラーなし
- [x] `uv run ruff format --check src/ tests/` エラーなし
- [x] `uv run mypy src/` エラーなし

---

## 実装後の振り返り

### 実装完了日
2026-02-26

### 計画と実績の差分

**計画と異なった点**:
- `_build_local_references()`の戻り値型(`dict[str, str]`)は変更せず、`_`プレフィックスのコンテキストキーを追加する方式を採用。当初はタプルや構造体を検討したが、既存テストと後方互換性を考慮しシンプルなdict拡張を選択
- OKE Node Pool用にdata source(`oci_core_images.oke_node`)を追加。Compute用とは別の名前空間で定義
- NAT Gatewayの自動生成を`_expand_vcn_network()`に追加（当初計画に含まれていたが、設計段階で明確化）

**新たに必要になったタスク**:
- なし。計画通りに全タスクを消化

**技術的理由でスキップしたタスク**:
- なし

### 学んだこと

**技術的な学び**:
- 単一の`var.subnet_id`に対してコンポーネントごとに異なる値を割り当てるには、テンプレートの文字列置換をグローバルからコンポーネントローカルに変更する必要がある
- public/privateの判定は、configの`prohibit_public_ip`（subnet）、`display_name`のキーワード（route_table, security_list）、サービスタイプ固有のconfig（LB, API GW）の3つの方式が混在。将来的にはConfigにexplicitな`network_tier`フィールドを持たせた方が堅牢
- OCI APIのリソース命名規則はサービスごとに異なる（NoSQLは英数字+`_`のみ、Object Storageは英数字+`-`+`_`、一般的なdisplay_nameはUTF-8許容）

**プロセス上の改善点**:
- フィードバックレポートから問題を分類→ステアリングファイル作成→フェーズ分け実装の流れが効率的だった
- テストを先に書かずに実装→テスト追加の順だったが、既存テストが全てパスしていたため安全に進められた

### 次回への改善提案
- connections定義の`deployed_in`関係をIaC生成でも活用し、サブネット割り当てをより正確にする（現状は名前ベースとサービスタイプベースの推測）
- バリデーションは`deployed_in`接続の有無に依存しすぎ。コンポーネント設定のみでの構造チェックも強化すべき
- テンプレートシステムの限界が見えてきた（条件付きブロック、動的参照等）。Jinja2等のテンプレートエンジン導入を検討
