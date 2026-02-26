# 設計書

## アーキテクチャ概要

README.mdとGitHub Actionsワークフローの追加。アプリケーションコードへの変更なし。

```
README.md  ──(Deploy button)──→  OCI Console RM
                                    ↓
GitHub Release (galley-stack.zip) ←── GitHub Actions (package-deploy-stack.yml)
                                    ↓
                              Terraform apply
                                    ↓
                              Container Instance + API Gateway + ...
```

## コンポーネント設計

### 1. README.md

**責務**:
- プロジェクト概要の提供
- Deploy to Oracle Cloudボタンの提供
- 前提条件と利用方法のドキュメント

**実装の要点**:
- Deploy buttonのSVGバッジURL: `https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg`
- RM stack作成URL: `https://cloud.oracle.com/resourcemanager/stacks/create?region=home&zipUrl=<PACKAGE_URL>`
- zipURL: `https://github.com/sogawa-yk/Galley/releases/latest/download/galley-stack.zip`
- latestリリースを使うことで、常に最新のTerraform設定を参照

### 2. GitHub Actions ワークフロー (`.github/workflows/package-deploy-stack.yml`)

**責務**:
- `deploy/`ディレクトリの内容をzip化
- GitHub Releaseに`galley-stack.zip`としてアップロード

**実装の要点**:
- トリガー: tagのpush (`v*`)
- `deploy/`ディレクトリ内で`zip`コマンド実行（ルートに.tfファイルが配置されるように）
- `gh release create`でリリース作成＆zipアップロード
- 既存リリースがある場合は`gh release upload --clobber`で上書き

### 3. 初回リリース

**責務**:
- GitHub Actionsが動く前に、手動でv0.1.0リリースを作成

**実装の要点**:
- ローカルで`deploy/`の中身をzip化
- `gh release create v0.1.0`でリリース作成＆zipアップロード

## データフロー

### ユーザーがDeployボタンをクリック
```
1. README.mdのDeployボタンをクリック
2. OCI Console RM のスタック作成画面に遷移（zipUrlパラメータ付き）
3. RMがGitHub Releaseからgalley-stack.zipをダウンロード
4. ユーザーが変数（compartment_ocid, region, vcn_id, subnet等）を入力
5. RMがTerraform applyを実行
6. Container Instance、API Gateway等が作成される
7. outputsからMCPエンドポイントURLが取得可能
```

## エラーハンドリング戦略

該当なし（アプリケーションコードの変更なし）。

## テスト戦略

### ユニットテスト
- 該当なし（アプリケーションコードの変更なし）

### 手動検証
- README.mdのDeployボタンリンクが正しいURLを指すこと
- GitHub Releaseにgalley-stack.zipが存在すること
- zip内のファイル構造が正しいこと（ルートに.tfファイル）

## 依存ライブラリ

新規追加なし。

## ディレクトリ構造

```
Galley/
├── README.md                                   # 新規作成
└── .github/
    └── workflows/
        └── package-deploy-stack.yml            # 新規作成
```

## 実装の順序

1. README.md作成
2. GitHub Actionsワークフロー作成
3. 初回リリース作成（手動）
4. Deployボタンの動作確認

## セキュリティ考慮事項

- GitHub Releaseは公開リポジトリでは誰でもアクセス可能（意図通り）
- zip内にシークレットや環境固有の情報を含めない
- `deploy/terraform.tfvars`は.gitignore対象のため含まれない

## パフォーマンス考慮事項

- 該当なし

## 将来の拡張性

- GitHub Actionsでのイメージビルド・OCIR pushの追加
- テスト自動実行の追加
- mainブランチへのpush時の自動リリース
