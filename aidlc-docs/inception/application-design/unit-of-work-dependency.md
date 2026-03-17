# Unit of Work Dependencies

## Dependency Matrix

| Unit | Depends On | Depended By | Shared Modules |
|---|---|---|---|
| U1: Hearing | (none) | U2, U4 | - |
| U2: TF Generation | U1 | U3 | - |
| U3: Infra Deployment | U2 | U5 | oci_cli.py (creates) |
| U4: App Generation | U1 | U5 | - |
| U5: App Deployment | U3, U4 | U6 | oci_cli.py (reuses) |
| U6: Verification | U5 | U7 | - |
| U7: Orchestration | U1-U6 | (entry point) | - |

## Development Dependency Graph

```
U1 (Hearing)
  |
  +---> U2 (TF Gen) ---> U3 (Infra Deploy)---+
  |                                           |
  +---> U4 (App Gen) ........................ |
                                              |
                      U5 (App Deploy) <-------+
                            |
                      U6 (Verification)
                            |
                      U7 (Orchestration)
```

## Development Order (End-to-End)

```
Phase 1: U1 Hearing          (独立、Python不要)
Phase 2: U2 TF Generation    (U1に依存、Python不要)
Phase 3: U3 Infra Deployment (U2に依存、oci_cli.py + oci_rm.py作成)
Phase 4: U4 App Generation   (U1に依存、Python不要)
Phase 5: U5 App Deployment   (U3,U4に依存、deployer.py作成)
Phase 6: U6 Verification     (U5に依存、e2e_runner.py作成)
Phase 7: U7 Orchestration    (全ユニットに依存、reporter.py作成)
```

## Parallel Execution at Runtime

```
Runtime:  U1 -> U2 -> [U3 || U4] -> U5 -> U6 -> U7(report)

Development: U1 -> U2 -> U3 -> U4 -> U5 -> U6 -> U7
                              (sequential, end-to-end)
```

- 開発時は順次（エンドツーエンド）
- 実行時はU3とU4が並行実行

## Integration Points

| From | To | Integration Data | Format |
|---|---|---|---|
| U1 -> U2, U4 | hearing result | `hearing/result.json` | JSON |
| U2 -> U3 | terraform files | `generated/{name}/terraform/` | HCL files |
| U3 -> U5 | infra outputs | `generated/{name}/stack_outputs.json` | JSON |
| U4 -> U5 | app code | `generated/{name}/app/` | Source files |
| U5 -> U6 | endpoints | `generated/{name}/endpoints.json` | JSON |
| U6 -> U7 | test results | `generated/{name}/test_results.json` | JSON |
