# 要求内容

## 概要

README.mdを作成し、OCI Resource Managerの「Deploy to Oracle Cloud」ボタンを配置して、ユーザーが自分のコンパートメントにGalleyを簡単にデプロイできるようにする。

## 背景

現在リポジトリにREADME.mdがなく、プロジェクトの概要やデプロイ方法が外部から把握できない。OCI Resource Managerの「Deploy to Oracle Cloud」ボタンを使えば、ユーザーはワンクリックでRM Console上にスタック作成画面を開き、必要な変数を入力するだけでGalleyをデプロイできる。

## 実装対象の機能

### 1. README.md
- プロジェクト概要（Galleyとは何か、何ができるか）
- Deploy to Oracle Cloudボタン
- 前提条件（VCN、サブネット、OCIRイメージ）
- デプロイ後の利用方法
- 開発者向けセットアップ手順

### 2. GitHub Actionsワークフロー
- `deploy/`ディレクトリの内容をzipにパッケージしてGitHub Releaseにアップロード
- RMはzipのルートに.tfファイルがある必要があるため、`deploy/`の中身のみをzip化
- mainブランチへのpush（deploy/配下の変更）またはリリースタグで自動実行

### 3. 初回リリースの作成
- GitHub Actionsが自動生成する前に、手動でgalley-stack.zipを作成しリリースする

## 受け入れ条件

### README.md
- [ ] プロジェクトの概要が記載されている
- [ ] Deploy to Oracle Cloudボタンが正しいURLで配置されている
- [ ] ボタンクリック時にOCI Console RM のスタック作成画面に遷移する
- [ ] 前提条件と入力変数の説明がある

### GitHub Actionsワークフロー
- [ ] deploy/配下の.tfファイルがルートに配置されたzipが生成される
- [ ] GitHub Releaseにgalley-stack.zipとしてアップロードされる

## 成功指標

- READMEのDeployボタンをクリックし、RM Console画面に遷移できる
- RM Console上でzipが正しく読み込まれ、変数入力画面が表示される

## スコープ外

- CI/CDパイプライン全体の構築（テスト・ビルド・OCIR push等）
- README.mdの多言語対応
- バッジ（CI status、coverage等）の追加

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書（F3: 配布用Terraform）
- `docs/environment.md` - 環境情報
- `docs/architecture.md` - 技術仕様書
- [Deploy to Oracle Cloud Button - Oracle Docs](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Tasks/deploybutton.htm)
