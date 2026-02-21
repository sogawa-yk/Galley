# タスクリスト: フィードバック修正

## フェーズ1: エラーメッセージ・レスポンス改善

- [x] `ArchitectureNotFoundError`のメッセージに`save_architecture`へのガイダンスを追加
- [x] `complete_hearing`ツールのレスポンスに`next_step`フィールドを追加
- [x] ~~上記変更に対するユニットテストの更新~~ (理由: 既存テストはエラーが発生すること自体を検証しており、メッセージ文字列は検証していないため、テスト更新は不要)

## フェーズ2: save_architectureのconnection ID解決

- [x] `DesignService.save_architecture`で仮ID→UUID マッピングを実装
- [x] connectionsのsource_id/target_idを実UUID に自動変換
- [x] connection ID解決のユニットテストを追加

## フェーズ3: export_iacのTerraformテンプレート改善

- [x] サービスタイプ→Terraformリソース名マッピング定義を追加
- [x] `export_iac`のcomponents.tf生成ロジックを動作するリソース定義に置き換え
- [x] HCL値のクォーティングをダブルクォートに修正
- [x] export_iacテンプレート改善のユニットテストを更新

## フェーズ4: export_iacのサーバー側ファイル書き出し

- [x] `StorageService`にセッションデータディレクトリパス取得メソッドを追加
- [x] `DesignService.export_iac`でTerraformファイルをサーバー側に書き出す
- [x] `export_iac`ツールのレスポンスに`terraform_dir`を追加
- [x] ファイル書き出しのユニットテストを追加

## フェーズ5: 自動terraform init

- [x] `InfraService._ensure_terraform_init`メソッドを実装
- [x] `run_terraform_plan`にinit自動実行を組み込み
- [x] `run_terraform_apply`にinit自動実行を組み込み
- [x] `run_terraform_destroy`にinit自動実行を組み込み
- [x] 自動initのユニットテストを追加

## フェーズ6: Terraform変数パラメータ

- [x] `InfraService.run_terraform_plan`に`variables`パラメータを追加
- [x] `InfraService.run_terraform_apply`に`variables`パラメータを追加
- [x] `InfraService.run_terraform_destroy`に`variables`パラメータを追加
- [x] ツール層(`tools/infra.py`)に`variables`パラメータを追加
- [x] 変数パラメータのユニットテストを追加

---

## 実装後の振り返り

### 実装完了日
2026-02-19

### 計画と実績の差分
- **仮ID解決**: 当初は全IDを再生成する方針だったが、既存テスト（UUIDをそのまま渡すケース）との互換性のため、UUID形式判定（`_is_uuid`メソッド）を導入し、仮IDのみ再生成する方式に変更した。
- **`_ensure_terraform_init`の`command`パラメータ**: 実装検証（implementation-validator）で、`command="plan"`がハードコードされている問題を指摘された。`calling_command`パラメータを追加し、`apply`/`destroy`から呼ばれた場合にも正しいコマンド名がレスポンスに含まれるよう修正した。
- **テスト更新（フェーズ1）**: 既存テストがエラーメッセージ文字列を検証していなかったため、テスト更新は不要と判断しスキップした。

### 学んだこと
- Pydanticの`model_validate`は`id`フィールドが渡されるとそのまま使用する。`default_factory`は値が未指定の場合のみ動作する。
- `json.dumps()`はHCLのダブルクォート生成に適している（`repr()`はシングルクォートを生成するためNG）。
- `.terraform`ディレクトリの存在確認がterraform init済みかどうかの標準的な判定方法。

### 次回への改善提案
- `export_iac`で生成される`variables.tf`に、使用するサービスタイプに応じた追加変数（`var.subnet_id`, `var.vcn_id`, `var.function_image`等）を動的に追加すると、生成直後に`terraform plan`が通るTerraformコードになる。
- `export_iac`のファイル書き出し時の`OSError`を`StorageError`でラップすると、エラーハンドリングが一貫する。
