# Unit Test Execution

## Run Unit Tests

### 1. Execute All Unit Tests
```bash
cd artifacts
uv run pytest tests/ -v
```

### 2. Run Tests with Coverage
```bash
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

### 3. Run Tests per Module
```bash
# OCI CLI
uv run pytest tests/test_oci_cli.py -v

# Resource Manager
uv run pytest tests/test_oci_rm.py -v

# Deployer
uv run pytest tests/test_deployer.py -v

# E2E Runner
uv run pytest tests/test_e2e_runner.py -v

# Reporter
uv run pytest tests/test_reporter.py -v
```

### 4. Review Test Results
- **Expected**: 23 tests pass, 0 failures
- **Test Report Location**: stdout (pytest default)

### Test Matrix

| Module | Tests | Description |
|---|---|---|
| test_oci_cli.py | 8 | CLI実行、コンパートメント/リージョン解決 |
| test_oci_rm.py | 6 | zip化、出力保存 |
| test_deployer.py | 2 | エンドポイント保存 |
| test_e2e_runner.py | 3 | レポート生成、テストスイート構造 |
| test_reporter.py | 4 | 進捗、サマリー、エラーレポート |
| **Total** | **23** | |

### Note on Mocking
- OCI CLI呼び出しはモックで実行（実OCI環境不要）
- HTTP リクエスト（e2e_runner）はモックで実行
- ファイルI/O（zip, JSON）は tmp_path で実行
