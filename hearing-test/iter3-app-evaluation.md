# Iteration 3: generate-app Skill Evaluation

**Scenario**: Python/Flask + OCI Functions (Serverless) + Object Storage (no DB)
**Date**: 2026-03-17
**Hearing Input**: Simulated JSON (image-resize-api)
**Comparison Baseline**: Iteration 1 (Python/FastAPI + Compute + ATP), Iteration 2 (Node.js/Express + Container Instances + MySQL)

---

## Execution Summary

| Item | Result |
|---|---|
| Output directory | `generated/image-resize-api/app/` |
| Language/Framework | Python 3.14 / Flask |
| Health endpoint | `GET /health` -> `{"status": "ok"}` |
| Unit tests (ImageProcessor) | 12 passed / 12 total |
| Integration tests (API) | 18 passed / 18 total |
| Total tests | **30 passed / 30 total** |
| Dockerfile | Generated with multi-stage build + HEALTHCHECK + non-root user |
| .dockerignore | Generated |
| func.yaml | Generated |
| func.py | Generated (OCI Functions entry point) |
| Self-correction loops used | 0 (all tests passed on first run) |

---

## Phase-by-Phase Evaluation

### Phase 1: Requirements Analysis

**Clarity**: 4/5 (unchanged from Iter 1/2)
**Completeness**: 4/5 (improved from 3.5/5 in Iter 2)
**Correctness**: 4/5 (unchanged)

**Observations**:
- The language/FW guidance table correctly pointed to `Flask` with `routes/`, `models.py`, `pytest`, `requirements.txt` -- directly actionable
- The DB strategy table was correctly identified as NOT APPLICABLE: hearing result has no `database` field, so no DB code was needed
- The `compute_type: "functions"` value correctly triggered the `serverless` path in the app_type table: "OCI Functions用のfunc.py/func.js + func.yaml"
- The `additional_services: ["object_storage", "api_gateway"]` field was partially useful -- Object Storage needed concrete code, but the skill provides NO guidance on how to implement Object Storage integration (mock vs real client, SDK usage, etc.)

**Gap -- app_type vs compute_type confusion**:
- The hearing result has `app_type: "api"` AND `compute_type: "functions"`. The skill's `app_type` table has a `serverless` row but this scenario is `api` deployed to Functions. The skill does not clearly explain how `compute_type: "functions"` interacts with `app_type: "api"` -- should I generate "REST APIエンドポイント群" (api row) or "OCI Functions用のfunc.py" (serverless row)? I generated BOTH (Flask API + func.py wrapper), which is the correct approach for API Gateway + Functions, but the skill should be explicit about this.

**What improved from Iter 1/2**:
- DB strategy guidance correctly led to skipping DB entirely (no SQLite fallback needed)
- Language/FW table gave immediate direction

---

### Phase 2: Application Code Generation

**Clarity**: 4/5 (unchanged)
**Completeness**: 3.5/5 (regression from 4/5 in Iter 2)
**Correctness**: 4/5 (unchanged)

**Observations**:
- Flask project structure guidance (`routes/`, `models.py`) was followed. Since there are no models in this project, `models.py` was correctly omitted.
- `/health` endpoint implemented as required.
- Port 8080 default with `PORT` env override: implemented.
- `sample_data.seed_required: false` correctly meant no seed logic was generated.
- No auth requirements meant no `seed-credentials.json` -- correct.
- `data-testid` not applicable (not a web app) -- correct.

**Functions-specific gaps (NEW findings for Iter 3)**:

| Gap | Severity | Description |
|---|---|---|
| No func.py guidance | HIGH | The skill says "OCI Functions用のfunc.py/func.js" but gives zero guidance on HOW to write func.py. No mention of fdk-python, no handler signature pattern, no guidance on wrapping Flask/FastAPI in a function handler. This required significant AI judgment. |
| No func.yaml schema guidance | MEDIUM | The skill says "func.yaml を生成" but does not describe the required fields (schema_version, name, runtime, entrypoint, memory, timeout, triggers). The entire func.yaml structure was invented by the AI. |
| No additional_services mapping | MEDIUM | `object_storage` was in the hearing result but the skill has no guidance on how to implement OCI Object Storage integration. No mention of oci SDK, mock patterns for local dev, or environment variables for configuration. |
| No API Gateway integration guidance | MEDIUM | `api_gateway` is in additional_services. The func.py needs to parse API Gateway headers (Fn-Http-Method, Fn-Http-Request-Url) to route requests correctly. The skill says nothing about this. |
| Dockerfile vs func.yaml conflict | LOW | For Functions deployment, the Dockerfile is technically not needed (Fn builds its own container). The skill always generates Dockerfile in Phase 4, but for `compute_type: "functions"`, func.yaml IS the build config. The skill should note this distinction. |
| No fdk dependency | LOW | `fdk` (Oracle's Function Development Kit) is not in the standard requirements.txt -- it's only available in the Fn runtime. The skill should mention this and advise not to include it in requirements.txt for local testing. |

**What improved from Iter 1/2**:
- The Python/Flask row in the guidance table provided correct structure direction
- No DB meant no SQLite fallback complexity -- the "missing DB strategy" gap from Iter 1 is not relevant here, proving the table works well for the no-DB case

---

### Phase 3: Test Generation and Execution

**Clarity**: 4.5/5 (unchanged from Iter 2)
**Completeness**: 4/5 (unchanged)
**Correctness**: 5/5 (unchanged)

**Observations**:
- Unit tests cover ImageProcessor thoroughly: both-dimensions, width-only, height-only, format conversion, RGBA-to-RGB, quality impact, error handling
- Integration tests cover all API endpoints: health, successful resize (JPEG/PNG/WebP), format conversion, validation errors (missing file, bad format, missing dimensions, invalid width/height/quality)
- Flask's `test_client()` used correctly (matching the skill's "テストクライアントを使用" instruction)
- LocalStorageClient (in-memory mock) used for test isolation -- no external dependencies needed
- All 30 tests passed on first run

**No-DB test simplification**:
- Without a database, there is no need for in-memory SQLite test isolation, conftest.py DB fixtures, or test-specific connection strings. The tests are simpler and more focused. The skill's DB-centric test guidance ("テスト用DBはインメモリSQLiteを使用") was correctly identified as N/A.

---

### Phase 4: Build Configuration

**Clarity**: 4.5/5 (unchanged from Iter 2)
**Completeness**: 3.5/5 (regression from 5/5 in Iter 2)
**Correctness**: 4/5 (unchanged)

**Observations**:
- **Dockerfile**: Generated with multi-stage build, HEALTHCHECK, non-root user, EXPOSE 8080 -- all per skill requirements
- **.dockerignore**: Generated with `.venv/`, `__pycache__/`, `*.pyc`, `tests/`, `.pytest_cache/` -- per skill requirements
- **func.yaml**: Generated as required. Contains schema_version, name, runtime, entrypoint, memory, timeout, triggers.
- **CMD path consistency**: `WORKDIR /app` + `COPY . .` + `CMD ["gunicorn", ..., "app:create_app()"]` is consistent

**Functions-specific Phase 4 issues**:

| Issue | Severity | Description |
|---|---|---|
| Dockerfile redundancy for Functions | MEDIUM | For `compute_type: "functions"`, OCI Functions uses func.yaml + Fn CLI to build. The Dockerfile is generated per Phase 4 rules but may never be used. The skill should make Dockerfile CONDITIONAL on compute_type. |
| No build.sh for Fn deployment | LOW | The skill mentions "build.sh をオプションで生成" but for Functions, the build command is `fn deploy --app <app-name>`, not `docker build`. No guidance on Fn-specific build scripts. |
| func.yaml completeness | LOW | Generated func.yaml works but the skill provides no guidance on memory/timeout tuning for image processing workloads. 1024MB memory and 120s timeout were chosen based on the hearing result's sizing, but this mapping is not documented in the skill. |

---

## Cross-Iteration Comparison

### Test Results Across Iterations

| Metric | Iter 1 (FastAPI) | Iter 2 (Express) | Iter 3 (Flask) |
|---|---|---|---|
| Unit tests | 4/4 | 11/11 | 12/12 |
| Integration tests | 21/21 | 24/24 | 18/18 |
| Total tests | 25/25 | 35/35 | 30/30 |
| Self-correction loops | 0 | 0 | 0 |
| First-run pass rate | 100% | 100% | 100% |

### Skill Improvement Trajectory

| Improvement (from Iter 1/2 feedback) | Tested in Iter 3? | Worked? |
|---|---|---|
| Language/FW guidance table | YES | YES - Flask row used correctly |
| DB local development strategy table | YES (no-DB case) | YES - correctly skipped DB code |
| .dockerignore generation | YES | YES - generated correctly |
| Non-root user in Dockerfile | YES | YES - appuser created and used |
| CMD path consistency guidance | YES | YES - WORKDIR/COPY/CMD aligned |
| In-memory SQLite for tests | N/A (no DB) | N/A |
| Seed data idempotent startup | N/A (seed_required=false) | N/A |
| Authentication patterns | N/A (no auth) | N/A |
| Template engine guidance | N/A (not web app) | N/A |

### NEW Issues Unique to Iter 3 (Serverless Path)

| Issue | Severity | Category |
|---|---|---|
| No func.py authoring guidance | HIGH | Functions-specific |
| No func.yaml schema documentation | MEDIUM | Functions-specific |
| No additional_services -> code mapping | MEDIUM | General |
| No API Gateway header parsing guidance | MEDIUM | Functions-specific |
| Dockerfile generated unnecessarily for Functions | MEDIUM | Conditional logic |
| app_type vs compute_type ambiguity | MEDIUM | Schema/design |
| No fdk dependency management guidance | LOW | Functions-specific |

---

## Overall Skill Assessment (Iteration 3)

| Dimension | Iter 1 | Iter 2 | Iter 3 | Notes |
|---|---|---|---|---|
| **Clarity** | 4.25/5 | 4.5/5 | 4.25/5 | Slight regression: Functions path ambiguity reduces clarity |
| **Completeness** | 3.5/5 | 4.25/5 | 3.75/5 | Regression: serverless path has major gaps (func.py, func.yaml, Object Storage) |
| **Correctness** | 4.25/5 | 4.75/5 | 4.25/5 | Regression: Dockerfile generated for Functions where it may not be needed |
| **Overall** | **4.0/5** | **4.5/5** | **4.0/5** | Functions path pulls score back to Iter 1 level |

---

## Generated File Inventory

```
generated/image-resize-api/app/
  app.py                # Flask app factory with /health, blueprint registration
  requirements.txt      # Flask, Pillow, oci, gunicorn, pytest
  func.py               # OCI Functions handler wrapping Flask app via fdk
  func.yaml             # OCI Functions configuration (memory, timeout, triggers)
  Dockerfile            # Multi-stage build, non-root user, HEALTHCHECK
  .dockerignore         # Excludes .venv, __pycache__, tests, .pytest_cache
  routes/
    __init__.py
    resize.py           # POST /api/resize with validation, processing, storage
  services/
    __init__.py
    image_processor.py  # Pillow-based resize with format conversion, quality control
    storage.py          # LocalStorageClient (mock) + OCIStorageClient (production)
  tests/
    __init__.py
    conftest.py         # Shared fixtures (app, client, sample images via Pillow)
    test_image_processor.py  # 12 unit tests for ImageProcessor
    test_api.py              # 18 integration tests for API endpoints
```

---

## Final Assessment: Skill Maturity After 3 Iterations

### What Works Well (Stable Across All Iterations)

1. **Core generation loop is solid**: All 3 iterations produced fully working, testable code with 100% first-run test pass rate
2. **Health endpoint**: Consistently implemented across FastAPI, Express, Flask
3. **Port configuration**: 8080 default + PORT env var -- works every time
4. **Test quality**: Good coverage of both happy path and error cases in every iteration
5. **Self-correction loop**: Not needed in any iteration (testament to code quality), but the mechanism exists

### What Improved Successfully (Iter 1 -> Iter 2 -> Iter 3)

1. **Language/FW guidance table**: Eliminates guesswork for project structure, ORM, test framework
2. **DB strategy table**: Works for both DB (Iter 1/2) and no-DB (Iter 3) cases
3. **.dockerignore**: Now consistently generated
4. **Non-root user**: Now consistently applied
5. **CMD path consistency**: No more path confusion

### Remaining Gaps (Priority Order)

| Priority | Gap | Affected Paths | Recommended Fix |
|---|---|---|---|
| **P0** | No func.py/func.js authoring guidance | Serverless | Add a "Serverless Functions" section with handler patterns for Python (fdk) and Node.js (fdk), including how to wrap Flask/Express/FastAPI |
| **P0** | No func.yaml schema guidance | Serverless | Add func.yaml template with required fields and explanations for memory/timeout/triggers |
| **P1** | app_type vs compute_type ambiguity | All serverless | Document the interaction: `app_type=api` + `compute_type=functions` means "generate API code + Functions wrapper" |
| **P1** | No additional_services -> code mapping | All | Add a table: `object_storage` -> oci SDK pattern with mock, `api_gateway` -> header parsing, `logging` -> language-specific logger |
| **P1** | Dockerfile should be conditional | Serverless | Make Dockerfile generation conditional: skip or mark optional when `compute_type=functions` |
| **P2** | No API Gateway header parsing guidance | Serverless | Document Fn-Http-Method, Fn-Http-Request-Url headers for request routing |
| **P2** | No fdk dependency guidance | Serverless | Note that fdk is available in Fn runtime only; exclude from requirements.txt for local testing |
| **P3** | No build.sh for Fn CLI | Serverless | Generate `fn deploy` script instead of `docker build` script for Functions |

### Maturity Rating

| Path | Maturity | Confidence |
|---|---|---|
| Python/FastAPI + Docker + DB | **Production-ready** | HIGH - well-guided, tested twice |
| Node.js/Express + Docker + DB | **Production-ready** | HIGH - well-guided, template/auth patterns solid |
| Python/Flask + Docker (no DB) | **Good** | MEDIUM - Flask row exists but Flask-specific patterns less tested |
| Python/Flask + Functions | **Prototype** | LOW - serverless path has major documentation gaps |
| Batch / Microservices | **Untested** | N/A - not evaluated in any iteration |

### Overall Skill Score: 4.2/5

The skill is mature for Docker-based deployments with databases (the most common path). The Iter 2 improvements to language guidance, DB strategy, and Dockerfile quality were significant and durable. However, the serverless Functions path exposes that the skill was primarily designed for container-based deployments. Bringing the Functions path to parity requires adding func.py patterns, func.yaml documentation, and conditional Dockerfile logic -- approximately 5-7 additions to the skill file.

The skill's fundamental architecture (4-phase pipeline with requirements -> code -> test -> build) is sound and adapts well to different scenarios. The main risk is not in the pipeline structure but in the per-technology guidance depth, which drops significantly for non-Docker deployment targets.
