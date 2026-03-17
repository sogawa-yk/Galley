# Component Dependencies

## Dependency Matrix

| Component | Depends On | Depended By |
|---|---|---|
| C-7: build-demo-env.md | C-1, C-2, C-3, C-4, C-5, C-6, C-12 | (entry point) |
| C-1: hearing.md | (none) | C-7 |
| C-2: generate-terraform.md | C-1 (hearing result) | C-3, C-7 |
| C-3: deploy-infra.md | C-2 (terraform), C-8, C-9 | C-5, C-7 |
| C-4: generate-app.md | C-1 (hearing result) | C-5, C-7 |
| C-5: deploy-app.md | C-3 (infra outputs), C-4 (app code), C-10, C-9 | C-6, C-7 |
| C-6: verify.md | C-5 (endpoints), C-11 | C-7 |
| C-8: oci_rm.py | C-9 | C-3 |
| C-9: oci_cli.py | (none - OCI CLI binary) | C-8, C-10, C-5 |
| C-10: deployer.py | C-9 | C-5 |
| C-11: e2e_runner.py | (none - requests library) | C-6 |
| C-12: reporter.py | (none) | C-7, all Skills |

## Data Flow

```
User (自然言語)
      |
      v
[C-1: hearing.md]
      |
      | hearing/result.json
      |
      +---------------------------+
      |                           |
      v                           v
[C-2: generate-terraform.md]   [C-4: generate-app.md]
      |                           |
      | generated/{name}/tf/      | generated/{name}/app/
      v                           | + unit/integration test
[C-3: deploy-infra.md]           |
      | C-8: oci_rm.py            |
      | C-9: oci_cli.py           |
      |                           |
      | stack_outputs.json        |
      +---------------------------+
                  |
                  v
         [C-5: deploy-app.md]
                  | C-10: deployer.py
                  | C-9: oci_cli.py
                  |
                  | endpoints.json
                  v
         [C-6: verify.md]
                  | C-11: e2e_runner.py
                  |
                  | test_results.json
                  v
         [C-12: reporter.py]
                  |
                  v
         summary.md (最終レポート)
```

## Communication Patterns

### Skill間のデータ受け渡し
Skills間のデータ受け渡しはファイルシステム経由で行う：

| From | To | Data | File Path |
|---|---|---|---|
| C-1 hearing | C-2 gen-tf, C-4 gen-app | ヒアリング結果 | `hearing/result.json` |
| C-2 gen-tf | C-3 deploy-infra | Terraformコード | `generated/{name}/terraform/` |
| C-3 deploy-infra | C-5 deploy-app | インフラ情報 | `generated/{name}/stack_outputs.json` |
| C-4 gen-app | C-5 deploy-app | アプリコード | `generated/{name}/app/` |
| C-5 deploy-app | C-6 verify | エンドポイント情報 | `generated/{name}/endpoints.json` |
| C-6 verify | C-12 reporter | テスト結果 | `generated/{name}/test_results.json` |

### Pythonモジュール間の呼び出し
- `oci_rm.py` → `oci_cli.py`: Resource Manager操作にOCI CLIを使用
- `deployer.py` → `oci_cli.py`: デプロイ操作にOCI CLIを使用
- 各モジュールは独立して動作可能（疎結合）

## Parallel Execution Map

```
Time -->

[hearing] -> [gen-tf] -> +---[deploy-infra (RM apply)]---+
                         |                               |
                         +---[gen-app -> test]--------+  |
                         |                            |  |
                         +----------------------------+--+
                                                      |
                                               [deploy-app] -> [verify] -> [report]
```

- **deploy-infra** と **gen-app + test** は並行実行
- 両方完了後に **deploy-app** を開始
- Claude Code Workflowの並行実行機能（バックグラウンドエージェント等）で実現
