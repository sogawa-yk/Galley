# Build Instructions

## Prerequisites
- **Python**: >= 3.11
- **uv**: パッケージマネージャー
- **Docker**: コンテナビルド用
- **OCI CLI**: OCI操作用（インスタンスプリンシパル認証環境）
- **Terraform**: >= 1.5（Resource Manager経由で実行するため直接は不要）

## Build Steps

### 1. Install Dependencies
```bash
cd artifacts
uv sync --extra dev
```

### 2. Verify Python Modules
```bash
uv run python -c "from src.oci_cli import run_command; print('oci_cli OK')"
uv run python -c "from src.oci_rm import create_stack; print('oci_rm OK')"
uv run python -c "from src.deployer import build_image; print('deployer OK')"
uv run python -c "from src.e2e_runner import health_check; print('e2e_runner OK')"
uv run python -c "from src.reporter import generate_summary; print('reporter OK')"
```

### 3. Run All Unit Tests
```bash
uv run pytest tests/ -v
```

### 4. Verify Build Success
- **Expected Output**: 23 tests passed, 0 failures
- **Build Artifacts**:
  - `artifacts/src/` — 5 Python modules
  - `artifacts/skills/` — 6 Skills + templates
  - `artifacts/workflows/` — 1 Workflow
  - `artifacts/tests/` — 5 test files + test scenarios

## Skill/Workflow Deployment

Skills/WorkflowsをClaude Codeで使用するには、以下の手順でコピーします：

```bash
# Skills
cp -r artifacts/skills/*.md /path/to/target/.claude/skills/
cp -r artifacts/skills/hearing-templates/ /path/to/target/.claude/skills/
cp -r artifacts/skills/tf-templates/ /path/to/target/.claude/skills/

# Workflows
cp -r artifacts/workflows/*.md /path/to/target/.claude/workflows/

# Python modules (Skill実行環境にコピー)
cp -r artifacts/src/ /path/to/target/src/
cp artifacts/pyproject.toml /path/to/target/
```

## Troubleshooting

### uv sync fails
- **Cause**: Python version mismatch
- **Solution**: `uv python install 3.12`

### Import errors
- **Cause**: Package not installed in editable mode
- **Solution**: `uv sync --extra dev` を再実行
