# Code Generation Plan - Unit 3: Infrastructure Deployment

## Unit Context
- **Unit**: Infrastructure Deployment
- **Requirements**: FR-5, FR-8, FR-11
- **Components**: C-3 deploy-infra.md (Skill), C-8 oci_rm.py, C-9 oci_cli.py
- **Dependencies**: Unit 2 (generated terraform files)
- **Output**: `generated/{project-name}/stack_outputs.json`

## Generation Steps

### Step 1: oci_cli.py — OCI CLI汎用ラッパー
- [x] `artifacts/src/oci_cli.py` を作成
- [x] `artifacts/tests/test_oci_cli.py` を作成

### Step 2: oci_rm.py — Resource Manager操作モジュール
- [x] `artifacts/src/oci_rm.py` を作成
- [x] `artifacts/tests/test_oci_rm.py` を作成

### Step 3: deploy-infra.md — Infrastructure Deployment Skill
- [x] `artifacts/skills/deploy-infra.md` を作成

### Step 4: テスト・ドキュメント
- [x] `aidlc-docs/construction/infra-deployment/code/code-summary.md` を作成
