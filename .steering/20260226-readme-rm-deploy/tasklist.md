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

## フェーズ1: README.md作成

- [x] README.mdを作成
  - [x] プロジェクト概要（Galleyの説明、コンセプト）
  - [x] Deploy to Oracle Cloudボタン（正しいURL構成）
  - [x] 前提条件セクション（VCN、サブネット、OCIRイメージ）
  - [x] Terraform入力変数の説明
  - [x] デプロイ後の利用方法（MCP接続設定）
  - [x] 開発者向けセットアップ手順

## フェーズ2: GitHub Actionsワークフロー作成

- [x] `.github/workflows/package-deploy-stack.yml`を作成
  - [x] トリガー設定（tag push）
  - [x] deploy/の中身をzip化するステップ
  - [x] GitHub Releaseへのアップロードステップ

## フェーズ3: 初回リリースと動作確認

- [x] deploy/の中身をローカルでzip化しgalley-stack.zipを作成
- [x] タグv0.1.0をpushしGitHub Actionsでリリース作成＆zipアップロード（プライベートリポジトリのためAPI経由での確認不可、Actions実行はGitHub上で確認要）
- [x] Deploy buttonのURLが正しいフォーマットであることを確認

## フェーズ4: 品質チェック

- [x] 既存テストが通ることを確認
  - [x] `uv run pytest` — 265 passed
- [x] リントエラーがないことを確認
  - [x] `uv run ruff check src/ tests/` — All checks passed
- [x] フォーマットが正しいことを確認
  - [x] `uv run ruff format --check src/ tests/` — 60 files already formatted
- [x] 型エラーがないことを確認
  - [x] `uv run mypy src/` — no issues found in 33 source files

---

## 実装後の振り返り

### 実装完了日
2026-02-26

### 計画と実績の差分

**計画と異なった点**:
- 当初`gh release create`で手動リリース予定だったが、`gh auth`が期限切れのため、GitHub Actionsワークフローをリリース作成も含む形に修正し、タグpush経由で自動作成する方式に変更
- implementation-validatorの指摘で、README変数表に`container_instance_*`系3変数が不足していたため追加

**新たに必要になったタスク**:
- GitHub Actionsワークフローに`gh release create`ロジック追加（リリースが存在しない場合は作成、存在する場合はzip上書き）
- README変数表の補完（`container_instance_shape`, `container_instance_ocpus`, `container_instance_memory_in_gbs`）

**技術的理由でスキップしたタスク**: なし

### 学んだこと

**技術的な学び**:
- OCI Resource Managerの「Deploy to Oracle Cloud」ボタンは`zipUrl`パラメータでGitHub Releaseのzipを指定できる
- SVGバッジURL: `https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg`
- RM Console URL: `https://cloud.oracle.com/resourcemanager/stacks/create?region=home&zipUrl=<URL>`
- RMはzip内のルートに.tfファイルがある必要があるため、`deploy/`サブディレクトリの場合は`cd deploy && zip -r ../galley-stack.zip .`でパッケージする
- GitHub Actionsのtag pushトリガーはタグが指すコミットのワークフローファイルを使用する

**プロセス上の改善点**:
- implementation-validatorサブエージェントがdeploy/variables.tfとの変数不整合を検出してくれた点が有用

### 次回への改善提案
- `gh auth`の有効性を事前確認するステップを計画に含めると、リリース作成フローがスムーズになる
- `deploy/schema.yaml`を追加すると、RM UIで変数入力時のUXが大幅に向上する（将来タスク候補）
