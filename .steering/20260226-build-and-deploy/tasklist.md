# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

---

## フェーズ1: モデル・サービス実装

- [x] `DeployResult`モデルにK8s関連フィールド追加（`k8s_manifests_dir`）
- [x] `AppService`にsubprocess実行ヘルパー`_run_subprocess`を追加
- [x] `AppService`にK8sマニフェスト生成メソッド`_generate_k8s_manifests`を実装
- [x] `AppService`にkubeconfig取得メソッド`_setup_kubeconfig`を実装
- [x] `AppService.build_and_deploy`を実装（cluster_id, image_uri, namespace引数追加）
- [x] `AppService.check_app_status`を実装（kubectl連携）

## フェーズ2: ツール層更新

- [x] `tools/app.py`の`build_and_deploy`ツールにパラメータ追加（cluster_id, image_uri, namespace）
- [x] ツールのdocstringを更新

## フェーズ3: テスト

- [x] `test_build_and_deploy_returns_not_implemented`を新しい実装に合わせて更新
- [x] K8sマニフェスト生成のユニットテスト追加
- [x] build_and_deployのsubprocess mokkテスト追加
- [x] check_app_statusのテスト更新

## フェーズ4: 品質チェック

- [x] `uv run pytest` — 274 passed
- [x] `uv run ruff check src/ tests/` — All checks passed
- [x] `uv run ruff format --check src/ tests/` — 60 files already formatted
- [x] `uv run mypy src/` — no issues found in 33 source files

---

## 実装後の振り返り

- **実装完了日**: 2026-02-26
- **計画と実績の差分**:
  - Docker buildは当初からスコープ外（Container Instance環境にDocker daemonなし）。`image_uri`を必須パラメータとし、ユーザー/CIが事前にビルド・プッシュする設計にした
  - 実装バリデーターで`self._storage._session_dir()`（プライベートメソッド）の使用を指摘され、公開メソッド`get_session_dir()`に修正した（4箇所）
- **学んだこと**:
  - `_generate_k8s_manifests`はDockerfileのEXPOSEからポート番号を自動検出する設計が有用
  - `_run_subprocess`は`asyncio.create_subprocess_exec`で実装。InfraServiceの既存パターン（`_run_oci_cli`）に準拠
  - kubeconfigは`--token-version 2.0.0`でResource Principal認証に対応可能
- **次回への改善提案**:
  - image_uri/namespaceの入力バリデーション追加を検討（現在は未実装）
  - app_nameのK8sラベル制約（RFC 1123）に対するサニタイズを検討
  - デプロイタイムアウト値（300s）の定数化を検討
