# 要求内容

## 概要

Phase 3「設計層」として、ヒアリング結果からOCIアーキテクチャを設計する機能群（F4〜F7）を実装する。

## 背景

Phase 1でヒアリング機能（F1, F2）を実装し、顧客要件を構造化できるようになった。Phase 2で配布基盤（F3）を構築した。次のステップとして、ヒアリング結果をインプットにOCIアーキテクチャを設計・検証・エクスポートする機能が必要。

## 実装対象の機能

### 1. F4: 自動設計モード
- LLMがヒアリング結果を分析し、推奨アーキテクチャを生成する際に、Galleyがプロンプトと保存ツールを提供
- `galley:save_architecture` で生成されたアーキテクチャを保存
- 生成されたアーキテクチャにはコンポーネント一覧、接続関係、推奨理由が含まれる

### 2. F5: 対話型設計モード
- `galley:add_component` でアーキテクチャにコンポーネントを追加
- `galley:remove_component` でコンポーネントを削除
- `galley:configure_component` でコンポーネントの詳細設定を変更
- `galley:list_available_services` で追加可能なOCIサービス一覧を取得
- 設計判断に対してフィードバックを返す

### 3. F6: アーキテクチャバリデーション
- `galley:validate_architecture` で現在の構成を検証し、問題点と推奨事項のリストを返す
- サービス間の接続要件（例：Private Endpoint必要性）を検出
- バリデーションルールはYAML形式で `config/validation-rules/` に管理

### 4. F7: エクスポート機能
- `galley:export_summary` で要件サマリーをMarkdownで出力
- `galley:export_mermaid` で構成図をMermaid形式で出力
- `galley:export_iac` でTerraformテンプレートを出力
- `galley:export_all` で全成果物を一括出力

## 受け入れ条件

### F4: 自動設計モード
- [ ] `galley:save_architecture` でアーキテクチャをセッションに保存できる
- [ ] 保存されたアーキテクチャにコンポーネント一覧と接続関係が含まれる
- [ ] ヒアリング完了済みセッションのみアーキテクチャ保存可能

### F5: 対話型設計モード
- [ ] `galley:add_component` でコンポーネントを追加できる
- [ ] `galley:remove_component` でコンポーネントを削除できる（関連接続も削除）
- [ ] `galley:configure_component` でコンポーネントの設定を変更できる
- [ ] `galley:list_available_services` でOCIサービス一覧を取得できる

### F6: アーキテクチャバリデーション
- [ ] `galley:validate_architecture` でバリデーション結果を返す
- [ ] バリデーションルールがYAMLで定義されている
- [ ] サービス間接続要件を検出できる

### F7: エクスポート機能
- [ ] `galley:export_summary` でMarkdown形式の要件サマリーを出力できる
- [ ] `galley:export_mermaid` でMermaid形式の構成図を出力できる
- [ ] `galley:export_iac` でTerraformテンプレートを出力できる
- [ ] `galley:export_all` で全成果物を一括出力できる

## 成功指標

- 全MCPツールがユニットテスト・統合テストをパスする
- `uv run pytest`, `uv run ruff check .`, `uv run mypy src/` が全てパスする
- 既存のヒアリング機能に影響を与えない

## スコープ外

以下はこのフェーズでは実装しません:

- OCI Object Storageへの実際の永続化（ローカルファイルシステムで代替）
- リージョン別サービス可用性の検証（バリデーションルール構造のみ用意）
- Terraform実行（F8, Phase 4）
- OCI CLI操作（F9, Phase 4）

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書（F4〜F7の定義）
- `docs/functional-design.md` - 機能設計書（データモデル、コンポーネント設計、ユースケース）
- `docs/architecture.md` - アーキテクチャ設計書（レイヤードアーキテクチャ、依存関係ルール）
- `docs/repository-structure.md` - リポジトリ構造定義書（ファイル配置規則）
- `docs/development-guidelines.md` - 開発ガイドライン（コーディング規約、テスト戦略）
