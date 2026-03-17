# Code Summary - Unit 3: Infrastructure Deployment

## Generated Files

| File | Type | Purpose |
|---|---|---|
| `artifacts/src/oci_cli.py` | Python | OCI CLI汎用ラッパー（コマンド実行、コンパートメント/リージョン解決） |
| `artifacts/src/oci_rm.py` | Python | Resource Manager操作（Stack CRUD、Plan/Apply/Destroy、ポーリング、ログ取得） |
| `artifacts/skills/deploy-infra.md` | Skill | インフラ構築Skill（自己修正ループ付きPlan/Apply） |

## Test Files

| File | Type | Purpose |
|---|---|---|
| `artifacts/tests/test_oci_cli.py` | Python Test | oci_cli.pyのユニットテスト（mock使用） |
| `artifacts/tests/test_oci_rm.py` | Python Test | oci_rm.pyのユニットテスト（zip化、出力保存） |

## Key Design Decisions

- **コンパートメント解決**: Instance Metadata → ENV → User Input のフォールバック
- **自己修正ループ**: Plan/Apply両方の失敗で最大2回リトライ（TFコード修正→zip再作成→Stack更新→再実行）
- **oci_cli.py は共有モジュール**: Unit 5 (App Deployment) でも再利用される

## Testing

### Python Unit Tests
```bash
cd artifacts && uv run pytest tests/test_oci_cli.py tests/test_oci_rm.py -v
```

### Agent Separation Test (DC-5)
1. **テストエージェント**: OCI環境でdeploy-infra.md Skillを実行、Unit 2の出力TerraformでStack作成→Apply
2. **評価エージェント**: Stack作成成功、Apply成功、stack_outputs.json生成を確認
