# Iteration 1: generate-app Skill Evaluation

**Scenario**: Python/FastAPI + Compute (Docker) + ATP
**Date**: 2026-03-17
**Hearing Input**: Simulated JSON (inventory-api)

---

## Execution Summary

| Item | Result |
|---|---|
| Output directory | `generated/inventory-api/app/` |
| Language/Framework | Python 3.12 / FastAPI |
| Health endpoint | `GET /health` -> `{"status": "ok"}` |
| Unit tests | 4 passed / 4 total |
| Integration tests | 21 passed / 21 total |
| Total tests | **25 passed / 25 total** |
| Dockerfile | Generated with multi-stage build + HEALTHCHECK |
| Self-correction loops used | 0 (all tests passed on first run) |

---

## Phase-by-Phase Evaluation

### Phase 1: Requirements Analysis

**Clarity**: 4/5
**Completeness**: 3/5
**Correctness**: 4/5

**Observations**:
- The skill clearly lists the fields to check from hearing result JSON
- The instruction "アプリの機能スコープを決定します" is vague -- it does not specify what output artifact or decision should be produced. There is no checkpoint or document to write.
- No guidance on how to map `database.type: "atp"` (Oracle ATP) to a local development strategy (e.g., use SQLite for local, oracledb for production). This was a gap I had to fill with my own judgment.
- Missing: guidance on what to do when `compute_new_or_existing` is "existing" vs "new"
- Missing: no instruction to validate the JSON schema or handle missing fields gracefully

**Improvements**:
1. Add explicit output: "Generate a brief requirements summary as a comment block or doc"
2. Add database mapping guidance: `atp` -> SQLAlchemy with SQLite locally, `mysql` -> SQLAlchemy with SQLite locally, etc.
3. Clarify what "機能スコープを決定" means in practice -- produce a bullet list? A file? A mental model?

---

### Phase 2: Application Code Generation

**Clarity**: 4/5
**Completeness**: 3/5
**Correctness**: 4/5

**Observations**:
- The generation guidelines are solid: `/health` endpoint, `DB_CONNECTION_STRING`, port 8080, `data-testid` for web apps
- The `app_type` table is helpful for knowing what to generate per type
- **Missing Python/FastAPI-specific guidance**:
  - No mention of project structure conventions (e.g., `routers/`, `models.py`, `schemas.py`, `database.py`)
  - No mention of Pydantic v2 vs v1 considerations
  - No mention of `@app.on_event("startup")` vs lifespan (the deprecated API was used; lifespan is the modern approach)
  - No guidance on ORM choice (SQLAlchemy is the de facto standard for FastAPI but not mentioned)
  - No mention of `__init__.py` files needed for Python packages
- **Missing for `sample_data`**: No guidance on when/how seeding should run (at startup? via CLI command? via endpoint?)
- No guidance on dependency management: `requirements.txt` vs `pyproject.toml` vs `poetry`

**Improvements**:
1. Add language-specific snippets or at minimum note: "Follow idiomatic project structure for the chosen language/framework"
2. Add: "For Python/FastAPI, use SQLAlchemy as ORM when database is required"
3. Add: "Use lifespan context manager instead of deprecated on_event for FastAPI >= 0.95"
4. Add: "For sample_data.seed_required=true, run seed at application startup (idempotently)"
5. Add: "Generate a requirements.txt (Python) or package.json (Node.js) with pinned dependency versions"

---

### Phase 3: Test Generation and Execution

**Clarity**: 4/5
**Completeness**: 4/5
**Correctness**: 5/5

**Observations**:
- Clear distinction between unit tests (models/business logic) and integration tests (API endpoints)
- The self-correction loop (max 3 attempts) is well-defined and practical
- Test result reporting format is clear
- **Good**: Specifies "テストクライアントを使用（HTTPリクエストではなくアプリ内部テスト）" -- this is important for FastAPI's TestClient approach
- **Missing**: No mention of test database isolation strategy (in-memory SQLite, fixtures, etc.)
- **Missing**: No mention of conftest.py or shared fixtures for pytest
- **Missing**: No guidance on test naming conventions
- **Minor**: The skill says "依存関係をインストール" but does not specify mechanism (pip, uv, poetry)

**Improvements**:
1. Add: "Use in-memory SQLite for test isolation, override DB dependency in fixtures"
2. Add: "Create conftest.py with shared fixtures (db_session, client)"
3. Add: "Install dependencies using the project's package manager before running tests"

---

### Phase 4: Build Configuration

**Clarity**: 5/5
**Completeness**: 4/5
**Correctness**: 4/5

**Observations**:
- Clear requirements: multi-stage build, HEALTHCHECK, EXPOSE 8080
- OCI Functions alternative (func.yaml) mentioned appropriately
- **Issue with Dockerfile placement**: The skill says `generated/{project_name}/app/Dockerfile` but the Dockerfile's `COPY . .` and `CMD ["uvicorn", "app.main:app", ...]` create a conflict -- if the Dockerfile is inside `app/`, the module path `app.main:app` won't resolve correctly because the working directory IS the app directory. The Dockerfile should either be at `generated/{project_name}/Dockerfile` (one level up) or the CMD should use `main:app` instead.
- **Missing**: No `.dockerignore` guidance (should exclude `.venv/`, `__pycache__/`, `*.pyc`, tests)
- **Missing**: No guidance on non-root user in container (security best practice)

**Improvements**:
1. Clarify Dockerfile location relative to app code and fix module path consistency
2. Add: "Generate .dockerignore to exclude test files, venv, cache"
3. Add: "Run as non-root user in the runtime stage"
4. Add: "For Python, consider using --no-cache-dir and --prefix for smaller images"

---

## Overall Skill Assessment

| Dimension | Score | Notes |
|---|---|---|
| **Clarity** | 4.25/5 | Instructions are well-structured and mostly unambiguous |
| **Completeness** | 3.5/5 | Missing language-specific guidance, DB strategy, dependency management |
| **Correctness** | 4.25/5 | Dockerfile path/module inconsistency; deprecated API used due to no version guidance |
| **Overall** | **4.0/5** | Produces working code but requires AI judgment to fill gaps |

---

## Generated File Inventory

```
generated/inventory-api/app/
  __init__.py
  main.py              # FastAPI app with /health, startup seed
  database.py          # SQLAlchemy engine, session, Base
  models.py            # Category, Product, InventoryRecord
  schemas.py           # Pydantic v2 request/response models
  seed.py              # Idempotent sample data seeding
  requirements.txt     # Pinned dependencies
  Dockerfile           # Multi-stage build with HEALTHCHECK
  routers/
    __init__.py
    categories.py      # CRUD for categories
    products.py        # CRUD for products
    inventory.py       # Stock in/out records with validation
  tests/
    __init__.py
    conftest.py         # Shared fixtures (in-memory DB, TestClient)
    test_models.py      # 4 unit tests for ORM models
    test_api.py         # 21 integration tests for all endpoints
```

---

## Top Priority Improvements for the Skill

1. **Add language-specific guidance sections** (or a reference table) covering:
   - Project structure conventions
   - ORM/DB library recommendations
   - Test framework and fixture patterns
   - Dependency file format

2. **Add database local development strategy**: Map each `database.type` value to a local testing approach (e.g., SQLite for ATP/MySQL/PostgreSQL in demo context)

3. **Fix Dockerfile module path consistency**: Clarify whether Dockerfile lives inside or outside the `app/` directory and adjust CMD accordingly

4. **Add `.dockerignore` generation** to Phase 4

5. **Add explicit Phase 1 output artifact**: Even a brief internal summary ensures traceability

6. **Modernize FastAPI patterns**: Recommend lifespan over deprecated `on_event`

7. **Specify dependency installation tool**: The skill should say "use uv, pip, or the project's package manager" rather than leaving it implicit
