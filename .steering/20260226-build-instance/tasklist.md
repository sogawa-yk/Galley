# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

---

## フェーズ1: Terraform構成

- [x] `deploy/build-instance.tf` — Compute Instance + cloud-init (Docker + OCI CLI)
- [x] `deploy/iam.tf` — Dynamic Group + Policy (Object Storage 読取り)
- [x] `deploy/variables.tf` — build_instance / OCIR 関連変数追加
- [x] `deploy/container-instance.tf` — Galleyに環境変数追加 (BUILD_INSTANCE_ID, OCIR_*)
- [x] `deploy/outputs.tf` — build_instance_id 出力追加

## フェーズ2: Python設定・サービス拡張

- [x] `src/galley/config.py` — ビルド関連設定フィールド追加
- [x] `src/galley/server.py` — AppServiceにconfigを渡す
- [x] `src/galley/services/app.py` — AppServiceコンストラクタ拡張 (config受取り)
- [x] `src/galley/services/app.py` — `_upload_app_tarball` メソッド実装
- [x] `src/galley/services/app.py` — `_build_and_push_image` メソッド実装
- [x] `src/galley/services/app.py` — `_wait_for_command` メソッド実装
- [x] `src/galley/services/app.py` — `build_and_deploy` を拡張 (image_uri オプショナル化)

## フェーズ3: ツール層更新

- [x] `src/galley/tools/app.py` — `image_uri` をオプショナルに変更 + docstring更新

## フェーズ4: テスト

- [x] 既存テストの修正 (AppService コンストラクタ変更に追従 — config=Noneで互換維持)
- [x] ビルドフロー (`_build_and_push_image`) のユニットテスト追加
- [x] `build_and_deploy` image_uri 未指定時のユニットテスト追加

## フェーズ5: 品質チェック

- [x] `uv run pytest` — 278 passed
- [x] `uv run ruff check src/ tests/` — All checks passed
- [x] `uv run ruff format --check src/ tests/` — 60 files already formatted
- [x] `uv run mypy src/` — no issues found in 33 source files

---

## 実装後の振り返り

- **実装完了日**: 2026-02-26
- **計画と実績の差分**:
  - バリデーターにより3つの重要な問題が検出され追加修正を実施:
    1. `iam.tf` にGalley Container Instance用のDynamic Group + `instance-agent-command-family`権限を追加
    2. cloud-initにOCI CLIインストールを追加
    3. OCIRトークンのbase64エンコードによるシェルインジェクション防止
  - `_wait_for_command`のステート判定に`CANCELED`/`TIMED_OUT`を追加
  - `compartment_id`未設定時のバリデーション追加
- **学んだこと**:
  - OCI Instance Agent Run Commandは`instance-agent-command-family`の`manage`権限が必要（呼び出し側）
  - シェルスクリプトにシークレットを埋め込む場合、base64エンコードが安全（シングルクォート等を含む値でも壊れない）
  - Terraform IAMリソース（Dynamic Group/Policy）は`tenancy_ocid`レベルのcompartmentに作成する必要がある
- **次回への改善提案**:
  - OCIR認証をInstance Principal + credential helper方式に移行すれば、auth tokenの受け渡しが不要になる
  - Build InstanceのOCI CLIはOracle Linux 8プラットフォームイメージにプリインストールされている可能性があるが、明示インストールで確実性を担保した
  - 将来的にKaniko方式に切り替える場合、Terraform側のBuild Instanceリソースを削除し、Dockerイメージにkanikoバイナリを同梱する形に変更する
