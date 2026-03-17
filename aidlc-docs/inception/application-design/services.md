# Services

## Service Layer Overview

このシステムではClaude Code Workflowがサービスオーケストレーション層として機能する。
各SkillがマイクロサービスのようにPythonモジュールを呼び出す。

```
+--------------------------------------------------------------+
|  S-1: Orchestration Service (build-demo-env.md Workflow)     |
|                                                              |
|  +----------+  +----------+  +----------+  +----------+     |
|  | hearing  |->| gen-tf   |->| deploy-  |->| verify   |     |
|  | .md      |  | .md      |  | app.md   |  | .md      |     |
|  +----------+  +----------+  +----------+  +----------+     |
|                     |                                        |
|                     v                                        |
|                +----------+                                  |
|                | deploy-  |                                  |
|                | infra.md |  (並行実行)                      |
|                +----------+                                  |
+--------------------------------------------------------------+
        |                |               |
        v                v               v
+-------------+  +-------------+  +-------------+
| S-2: OCI    |  | S-3: Build  |  | S-4: Test   |
| Infra Svc   |  | Deploy Svc  |  | Service     |
| (oci_rm.py  |  | (deployer   |  | (e2e_runner |
|  oci_cli.py)|  |  .py)       |  |  .py)       |
+-------------+  +-------------+  +-------------+
```

## S-1: Orchestration Service

- **Implementation**: `build-demo-env.md` (Claude Code Workflow)
- **Responsibility**: 全フェーズの順序制御と並行実行管理
- **Orchestration Pattern**:

```
Sequential: hearing -> generate-terraform
Parallel:   deploy-infra || (generate-app -> unit-test -> integration-test)
Sequential: (parallel完了後) deploy-app -> verify
Sequential: (全完了後) summary report
```

- **Error Handling**:
  - 各フェーズの成否を確認して次フェーズに進む
  - 失敗時はClaude Codeの判断力でリカバリーを試行
  - リカバリー不能時はユーザーに状況を報告

## S-2: OCI Infrastructure Service

- **Implementation**: `oci_rm.py` + `oci_cli.py` (Python Modules)
- **Responsibility**: OCIリソースの操作全般
- **Consumers**: deploy-infra.md, deploy-app.md
- **Key Operations**:
  - Resource Manager Stack CRUD
  - OCI CLI汎用操作（リソース参照、ステータス確認）
  - コンパートメント・リージョン情報取得

## S-3: Build & Deploy Service

- **Implementation**: `deployer.py` (Python Module)
- **Responsibility**: コンテナビルド・レジストリプッシュ・デプロイ実行
- **Consumers**: deploy-app.md
- **Key Operations**:
  - Dockerイメージビルド
  - OCIRプッシュ
  - OKE / Container Instances / Functions デプロイ

## S-4: Test Service

- **Implementation**: `e2e_runner.py` (Python Module)
- **Responsibility**: デプロイ後のE2Eテスト実行
- **Consumers**: verify.md
- **Key Operations**:
  - ヘルスチェック
  - APIテスト
  - テストレポート生成

## S-5: Reporting Service

- **Implementation**: `reporter.py` (Python Module)
- **Responsibility**: 進捗報告と最終レポート生成
- **Consumers**: build-demo-env.md (Workflow), 各Skill
- **Key Operations**:
  - フェーズ進捗レポート
  - 最終サマリー（環境URL、Stack OCID、リソース一覧）
  - エラーレポート
