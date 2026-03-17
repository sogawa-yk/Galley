# Final Quality Test: Python/Flask + Functions + Object Storage + API Gateway

**Date**: 2026-03-17
**Scenario**: Iteration 3 - Functions compute with API Gateway and Object Storage

## Test Results

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | hearing: container="functions" auto-set when compute_type=functions | **PASS** | hearing.md L74: "コンピュート種別が Functions の場合、コンテナ化方式の質問は省略し `container: "functions"` を自動設定する" |
| 2 | hearing: container question skipped for Functions | **PASS** | hearing.md L74-75: Functions時は省略、それ以外は必ず提示と明記 |
| 3 | generate-terraform: Functions template includes both oci_functions_application AND oci_functions_function | **PASS** | compute-templates.md L118-144: 両リソースが定義済み。L148: "`oci_functions_application` だけでは不十分。`oci_functions_function` も必ず定義すること" |
| 4 | generate-terraform: API Gateway template exists with /health route | **PASS** | apigateway-template.md L34-43: `/health` ルートが明示的に定義。L78: "必ず含めること" と注意事項にも記載 |
| 5 | generate-terraform: outputs include functions_invoke_endpoint and api_gateway_url | **PASS** | outputs-template.md L88-91: `functions_invoke_endpoint` 定義済み。L97-101: `api_gateway_url` 定義済み。generate-terraform.md L23-24にも出力契約として明記 |
| 6 | generate-terraform: No DB resources when no database | **PASS** | generate-terraform.md L181: "database.tf（DB要求時のみ生成）"。Phase 1マッピング表もdatabase条件付き |
| 7 | generate-terraform: Object Storage resource generated for additional_services | **PASS** | generate-terraform.md L54: additional_servicesマッピングに `object_storage -> oci_objectstorage_bucket` 明記 |
| 8 | generate-app: api+functions combination guidance (Flask wrapped with fdk) | **PASS** | generate-app.md L92: "`app_type: api` + `compute_type: functions` -> Flask/FastAPI APIをOCI Functions handlerでラップ。`func.py`でfdkを使用してFlaskアプリをハンドラーとして登録。" |
| 9 | generate-app: Dockerfile skipped for compute_type=functions | **PASS** | generate-app.md L134: "`compute_type: functions` の場合はスキップ -- `fn deploy` が `func.yaml` を使用してビルドするため、別途Dockerfileは不要" |
| 10 | generate-app: func.yaml mentioned in Phase 4 | **PASS** | generate-app.md L143: "OCI Functions の場合: `func.yaml` を生成" (Phase 4, item 3) |
| 11 | deploy-app: Phases 2/2.5/3 skipped for Functions | **PASS** | deploy-app.md L59: "Functions の場合: Phase 2, Phase 2.5, Phase 3 をスキップし、直接 Phase 3.5 に進んでください" |
| 12 | deploy-app: func.yaml config injection for env_vars | **PASS** | deploy-app.md L267-276: func.yamlのconfig:セクションにenv_varsを書き込むYAMLコード明記 |
| 13 | deploy-app: fn deploy uses app_name (project_name), not OCID | **PASS** | deploy-app.md L282: `function_app_id=project_name,  # アプリ名を使用`。deployer.py L189: param名 `app_name`、L197-198: docstring "Functions Application name (NOT OCID)" |
| 14 | deploy-app: API Gateway URL endpoint resolution (priority over Functions invoke) | **PASS** | deploy-app.md L289-296: `if stack_outputs.get("api_gateway_url"):` が最優先。Phase 5 L317-326にも優先順位リスト明記 |
| 15 | deploy-app: deployer.py deploy_to_functions param is app_name (not function_app_id) | **PASS** | deployer.py L189: `def deploy_to_functions(app_dir: str, app_name: str, function_name: str)` -- パラメータ名は `app_name` |
| 16 | verify: Functions + APIGW health check guidance | **PASS** | verify.md L40-41: "Functions + API Gateway の場合: ヘルスチェックURLは API Gateway 経由のURL + `/health` パスを使用" |
| 17 | verify: binary response handling in e2e_runner (_safe_json) | **PASS** | e2e_runner.py L199-211: `_safe_json` がcontent-typeチェックしバイナリ時は `[binary: {content_type}, {size} bytes]` を返却 |
| 18 | workflow: sequential execution (no parallel ambiguity) | **PASS** | build-demo-env.md: Steps 1-7が全て `---` で区切られ順次実行。各ステップにエラーゲート。並列実行の記述なし |

## Summary

**18 / 18 PASS** -- All checks passed.

### Note on deploy-app.md skill-to-code parameter mismatch

deploy-app.md L283 calls `deploy_to_functions(... function_app_id=project_name ...)` using keyword `function_app_id`, but deployer.py's actual signature uses `app_name`. This is a minor documentation inconsistency in the skill file's example code (the function will receive the value correctly as positional arg, but the keyword name differs). Not a blocking issue since the skill file comments say "# アプリ名を使用" and deployer.py enforces the correct semantics. Consider aligning the keyword arg name in deploy-app.md to `app_name` for consistency.
