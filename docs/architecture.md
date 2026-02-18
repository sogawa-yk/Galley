# 技術仕様書 (Architecture Design Document)

## テクノロジースタック

### 言語・ランタイム

| 技術 | バージョン |
|------|-----------|
| Python | 3.12+ |
| uv | 最新安定版 |

**Python 3.12+ の選定理由**:
- OCI SDK for Pythonの公式サポート対象
- FastMCPの対応言語
- dataclass、型ヒント、asyncioなどの言語機能が成熟
- `type` 文（PEP 695）による型エイリアス構文の改善、パフォーマンス向上（Comprehension inlining等）

### フレームワーク・ライブラリ

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| FastMCP | 最新安定版 | MCPサーバーフレームワーク | Python向けMCPサーバー実装の標準。SSE/StreamableHTTP対応 |
| OCI SDK for Python | 最新安定版 | OCI APIアクセス | OCI公式SDK。Resource Principal認証対応 |
| Pydantic | 2.x | データバリデーション・シリアライゼーション | 型安全なデータモデル定義、JSONスキーマ自動生成 |
| pydantic-settings | 2.x | 環境変数ベースの設定管理 | BaseSettingsによる設定クラス。pydanticとは別パッケージ |
| PyYAML | 6.x | YAML設定ファイル読み込み | バリデーションルール・サービス定義の読み込み |
| uvicorn | 最新安定版 | ASGIサーバー | FastMCPのHTTPトランスポート用 |

### 同梱ツール（コンテナイメージ内）

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| OCI CLI | 最新安定版 | OCI汎用コマンド実行 | `run_oci_cli` ツールで利用。OCI公式CLI |
| Terraform | 1.x | IaCによるリソースプロビジョニング | OCI Provider対応。業界標準のIaCツール |
| OCI Terraform Provider | 最新安定版 | Terraform用OCIプロバイダー | OCI公式。全OCIサービスをカバー |
| kubectl | 最新安定版 | OKEクラスター操作 | Kubernetes標準CLI |

### 開発ツール

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| uv | 最新安定版 | パッケージ管理・仮想環境 | 高速なPythonパッケージマネージャー。pip互換 |
| pytest | 8.x | テストフレームワーク | Python標準のテストフレームワーク。豊富なプラグインエコシステム |
| pytest-asyncio | 最新安定版 | 非同期テスト | async/awaitテストのサポート |
| Ruff | 最新安定版 | リンター・フォーマッター | 高速なPythonリンター。Black互換フォーマット |
| mypy | 最新安定版 | 型チェック | Pythonの静的型検査 |
| Docker | 最新安定版 | コンテナビルド | コンテナイメージのビルド・テスト |

## アーキテクチャパターン

### レイヤードアーキテクチャ

```
┌──────────────────────────────────────────────┐
│   MCPプロトコル層                               │ ← FastMCPがMCPプロトコルを処理
│   (ツール登録・呼び出しルーティング)               │
├──────────────────────────────────────────────┤
│   サービス層                                    │ ← ビジネスロジック
│   (Hearing / Design / Infra / App)            │
│                                              │
│   ┌────────────────────────┐                 │
│   │ ArchitectureValidator  │ ← サービス層・    │
│   │ (バリデーション専用)     │   データアクセス層  │
│   └────────────────────────┘   の両方に依存可能 │
├──────────────────────────────────────────────┤
│   データアクセス層                               │ ← データ永続化・外部サービス連携
│   (StorageService / OCIClientFactory)         │
├──────────────────────────────────────────────┤
│   外部システム                                   │ ← OCI Object Storage / OCI API
│   (Object Storage / Resource Manager / OKE)    │
└──────────────────────────────────────────────┘
```

**ArchitectureValidatorの位置付け**: validators/ はサービス層とデータアクセス層の両方に依存可能なクロスカッティングコンポーネント。services/ から呼び出され、storage/ からバリデーションルールを読み込む。ただし validators/ → services/ の依存は禁止（循環依存防止）。

#### MCPプロトコル層
- **責務**: MCPプロトコルの処理、ツール・リソース・プロンプトの登録と呼び出しルーティング
- **許可される操作**: サービス層の呼び出し
- **禁止される操作**: データアクセス層への直接アクセス、外部システムへの直接アクセス

#### サービス層
- **責務**: ビジネスロジックの実装（ヒアリング管理、設計管理、インフラ構築、アプリデプロイ）
- **許可される操作**: データアクセス層の呼び出し、サービス間の呼び出し
- **禁止される操作**: MCPプロトコル層への依存

#### データアクセス層
- **責務**: OCI Object Storageへのデータ永続化、OCI SDKクライアントの管理
- **許可される操作**: 外部システム（Object Storage、OCI API）へのアクセス
- **禁止される操作**: ビジネスロジックの実装

## データ永続化戦略

### ストレージ方式

| データ種別 | ストレージ | フォーマット | 理由 |
|-----------|----------|-------------|------|
| セッションデータ | OCI Object Storage | JSON | 構造化データの柔軟な格納。LLMが解釈しやすい |
| Terraform state | OCI Object Storage | JSON (tfstate) | Terraform標準のリモートstate管理 |
| テンプレート | OCI Object Storage | 各種（テンプレートファイル群） | 開発者が随時追加・更新可能 |
| バリデーションルール | OCI Object Storage | YAML | 人間が読み書きしやすく、構造化データに適する |
| サービス定義 | OCI Object Storage | YAML | バリデーションルールと同様 |
| アプリスナップショット | OCI Object Storage | アーカイブ（tar.gz） | ロールバック用のコード全体保存 |

### キャッシュ戦略

- **セッションデータ**: メモリ上にキャッシュ。変更時のみObject Storageに書き込み
- **バリデーションルール**: 起動時にObject Storageから読み込み、メモリにキャッシュ（TTL: 10分）
- **サービス定義**: バリデーションルールと同じキャッシュ方式
- **テンプレートメタデータ**: `list_templates` 呼び出し時にキャッシュ（TTL: 5分）

### Terraform state の排他制御

- **方針**: 単一ユーザー前提のため、ファイルロックによる排他制御は実装しない
- **安全策**: Terraformコマンド実行中（plan / apply / destroy）は、同一セッションに対する他のTerraform操作をインメモリフラグで排他する
- **state保存**: apply / destroy 完了時にObject Storageに書き込み。バージョニング機能により前バージョンを保持

### 同時リクエスト処理

- **方針**: Galleyは単一ユーザー利用を前提とするが、MCPプロトコルの仕様上、複数ツール呼び出しが同時に到着する可能性がある
- **軽量操作**（セッションCRUD、バリデーション等）: asyncioにより並行処理
- **重量操作**（Terraform実行、OCI CLI実行）: セッション単位のasyncio.Lockで逐次処理。実行中に同一セッションへの重量操作リクエストが来た場合はエラーを返す

### バックアップ戦略

- **頻度**: セッションデータは変更の都度Object Storageに永続化（即時）
- **スナップショット**: アプリケーションコードのカスタマイズ前に自動保存
- **Terraform state**: apply成功時に自動保存。前バージョンをバージョニングで保持
- **復元方法**: `StorageService.restore_snapshot()` によるロールバック

## パフォーマンス要件

### レスポンスタイム

| 操作 | 目標時間 | 測定環境 |
|------|---------|---------|
| MCPツール呼び出し（軽量操作） | 3秒以内 | Container Instance（1 OCPU / 2GB） |
| セッションCRUD操作 | 1秒以内 | Container Instance（1 OCPU / 2GB） |
| Object Storage読み書き | 2秒以内 | 同一リージョン内通信 |
| `terraform plan`（10リソース以下） | 60秒以内 | Container Instance（1 OCPU / 2GB） |
| `terraform apply`（10リソース以下） | 5分以内 | OCI APIの処理時間依存 |
| バリデーション実行 | 5秒以内 | ルール100件以下の構成 |

### リソース使用量

| リソース | 上限 | 理由 |
|---------|------|------|
| メモリ | 2GB | Container Instanceの最小構成。Terraform実行を含む |
| OCPU | 1 | 単一ユーザー利用を前提とした最小構成 |
| ディスク | 10GB | コンテナイメージ + Terraformワークスペース + 一時ファイル |

## セキュリティアーキテクチャ

### 認証

#### OCI認証（Resource Principal）

```
Container Instance
  └─ Dynamic Group（一致ルール: instance.id = 'ocid1.instance...'）
       └─ IAM Policy
            ├─ Allow: Object Storage管理（galley-bucket）
            ├─ Allow: Resource Manager管理（galley_work_compartment_id）
            ├─ Allow: Container Instances読み取り
            ├─ Allow: VCN / Subnet管理（galley_work_compartment_id）
            ├─ Allow: Compute管理（galley_work_compartment_id）
            └─ Allow: その他検証リソース（galley_work_compartment_id）
```

- Resource Principal認証によりAPIキーをコンテナに保持しない
- Dynamic Groupの一致ルールをContainer InstanceのOCIDで限定
- IAM Policyで操作対象を `galley_work_compartment_id` 内に限定

#### MCPエンドポイント認証（URLトークン）

```
MCPホスト → HTTPS → API Gateway → URLトークン検証 → Container Instance
```

- API GatewayがHTTPS終端を担当（利用者側でドメイン・証明書不要）
- URLトークンは `terraform apply` 時にランダム生成
- トークンはTerraform outputとして出力

### データ保護

- **通信暗号化**: API Gateway〜MCPホスト間はHTTPS（TLS 1.2+）
- **データ暗号化**: Object StorageはOCIのサーバーサイド暗号化（SSE）を使用
- **アクセス制御**: IAM Policyによるコンパートメント単位のアクセス制御

### 入力検証

- **MCPツールパラメータ**: Pydanticモデルによるバリデーション
- **OCI CLIコマンド**: ホワイトリスト方式でコマンドを検証。シェルインジェクション防止
- **Terraformファイル**: ファイルパスのディレクトリトラバーサル防止
- **テンプレートカスタマイズ**: `protected_paths` で保護されたファイルへの変更を拒否

### 権限分離

- Galleyの操作対象を `galley_work_compartment_id` 内に限定
- Galley自体のインフラ（Container Instance、API Gateway等）は別コンパートメントに配置
- 利用者のOCIサービスリミットが追加の安全装置として機能

## スケーラビリティ設計

### データ増加への対応

- **想定データ量**: セッション数100〜1000件、テンプレート数10〜50件、バリデーションルール数50〜200件
- **パフォーマンス劣化対策**: Object Storageのプレフィックスベースのデータ分割。セッションデータはセッションIDで分離
- **アーカイブ戦略**: 古いセッションデータの自動削除は実装しない（Object Storageのライフサイクルポリシーで対応可能）

### 機能拡張性

- **テンプレートストア**: Object Storageの所定ディレクトリにファイルをアップロードするだけで追加可能
- **バリデーションルール**: YAMLファイルの追加・編集で拡張可能
- **OCIサービス定義**: `oci-services.yaml` の編集で対応サービスを追加可能
- **MCPツール**: FastMCPのデコレータベースのツール登録で容易に追加可能

### 将来のスケールアップ

- Container InstanceのOCPU/メモリ増強で垂直スケーリング可能
- マルチユーザー対応時はContainer Instanceの複数起動 + ロードバランサー追加を検討

## テスト戦略

### ユニットテスト
- **フレームワーク**: pytest + pytest-asyncio
- **対象**: 各サービスクラスのメソッド、バリデーションルール適用ロジック、データモデルのバリデーション
- **カバレッジ目標**: 80%
- **モック**: OCI SDKクライアント、Object Storageアクセス、外部プロセス実行（Terraform/OCI CLI）

### 統合テスト
- **方法**: FastMCPのInMemoryTransportを使用したMCPプロトコル経由のテスト
- **対象**: MCPツール呼び出し→サービス層→ストレージ層の連携

### E2Eテスト
- **ツール**: pytest + 実際のOCI環境（テスト用コンパートメント）
- **シナリオ**: ヒアリング〜設計〜Terraform plan/applyの一連フロー
- **実行タイミング**: リリース前の手動実行（OCI環境依存のため）

## 技術的制約

### 環境要件
- **実行環境**: OCI Container Instance（ARM64 / AMD64）
- **最小メモリ**: 2GB（Terraform実行を含む）
- **最小OCPU**: 1
- **必要ディスク容量**: 10GB（コンテナイメージ + ワークスペース）
- **必要な外部依存**: OCI API（Resource Principal認証経由）、Object Storage

### パフォーマンス制約
- Container Instanceは単一コンテナでの実行。同時リクエスト処理はasyncioで対応するが、CPU集約処理（Terraform実行等）は逐次処理
- Object StorageへのAPIコールにはネットワークレイテンシが発生。キャッシュで緩和

### セキュリティ制約
- Resource Principal認証はOCI Container Instance内でのみ利用可能。ローカル開発時はAPI Key認証にフォールバック
- URLトークン認証はベーシックな認証方式。IdPが利用可能な環境ではOAuth認証への移行を推奨

### ローカル開発時の認証フォールバック

ローカル開発環境ではResource Principalが利用できないため、以下の順序で認証を試行する:

1. **Resource Principal**（環境変数 `OCI_RESOURCE_PRINCIPAL_VERSION` が設定されている場合）
2. **API Key認証**（`~/.oci/config` のデフォルトプロファイル）

`OCIClientFactory` がインスタンス化される際に上記の順序で認証を試行し、最初に成功した方式を使用する。API Key認証の設定方法は `oci setup config` コマンドで事前にOCI CLIの設定を完了させる必要がある。

## 依存関係管理

| ライブラリ | 用途 | バージョン管理方針 |
|-----------|------|-------------------|
| fastmcp | MCPサーバーフレームワーク | 互換範囲指定（`>=x.y,<x+1`） |
| oci | OCI SDK for Python | 互換範囲指定 |
| pydantic | データバリデーション | メジャーバージョン固定（`>=2.0,<3`） |
| pydantic-settings | 環境変数ベース設定管理 | メジャーバージョン固定（`>=2.0,<3`）。pydanticとは別パッケージ |
| pyyaml | YAML処理 | 互換範囲指定 |
| uvicorn | ASGIサーバー | 互換範囲指定 |
| pytest | テストフレームワーク | 開発依存。互換範囲指定 |
| ruff | リンター・フォーマッター | 開発依存。最新版 |
| mypy | 型チェック | 開発依存。互換範囲指定 |

**方針**:
- 本番依存は互換範囲指定で安定性を確保
- 開発依存は比較的緩い範囲指定
- `uv.lock` で再現可能なビルドを保証
