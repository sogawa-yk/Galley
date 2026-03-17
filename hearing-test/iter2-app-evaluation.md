# Iteration 2: generate-app Skill Evaluation

**Scenario**: Node.js/Express + Container Instances + MySQL (EJS web app with auth)
**Date**: 2026-03-17
**Hearing Input**: Simulated JSON (ticket-system-demo)
**Comparison Baseline**: Iteration 1 (Python/FastAPI + Compute + ATP)

---

## Execution Summary

| Item | Result |
|---|---|
| Output directory | `generated/ticket-system-demo/app/` |
| Language/Framework | Node.js 20 / Express |
| View Engine | EJS (server-side rendering) |
| Health endpoint | `GET /health` -> `{"status": "ok"}` |
| Unit tests (models) | 11 passed / 11 total |
| Integration tests (API) | 24 passed / 24 total |
| Total tests | **35 passed / 35 total** |
| Dockerfile | Generated with multi-stage build + HEALTHCHECK + non-root user |
| .dockerignore | Generated |
| Self-correction loops used | 0 (all tests passed on first run) |

---

## Phase-by-Phase Evaluation

### Phase 1: Requirements Analysis

**Clarity**: 4/5 (unchanged from Iter 1)
**Completeness**: 3.5/5 (improved from 3/5)
**Correctness**: 4/5 (unchanged)

**Observations**:
- The language/framework guidance table was useful -- it immediately pointed to `Sequelize` as ORM and `Jest` as test framework for Node.js/Express, removing ambiguity that existed in Iteration 1
- The DB local development strategy table correctly mapped `mysql` -> SQLite locally with Sequelize, which worked perfectly
- The `custom_requirements` field was clear enough to drive the feature set (auth, tickets, projects, EJS)
- Still no guidance on how to map `compute_new_or_existing` or `additional_services` (e.g., "logging") to concrete code patterns

**What improved from Iter 1**:
- DB strategy table eliminated the guesswork that Iter 1 had for ATP -> SQLite mapping
- Language/FW guidance table gave clear direction on project structure (`routes/`, `models/`, `middleware/`)

---

### Phase 2: Application Code Generation

**Clarity**: 4.5/5 (improved from 4/5)
**Completeness**: 4/5 (improved from 3/5)
**Correctness**: 4.5/5 (improved from 4/5)

**Observations**:
- The language/FW guidance table (`routes/`, `models/`, `middleware/` for Express) was directly actionable and followed exactly
- `data-testid` guidance for web apps was explicitly stated and followed -- 30+ data-testid attributes applied across all EJS templates
- Seed data guidance (`seed_required=true` -> idempotent startup seed) was clear and directly implemented: seed checks `User.count() > 0` before inserting
- DB_CONNECTION_STRING fallback to SQLite worked correctly for both app runtime and test execution
- Port 8080 default with `PORT` env var override: implemented correctly

**What improved from Iter 1**:
- Iter 1 lacked language-specific guidance, causing the AI to choose patterns independently. Iter 2's table gave concrete direction (Sequelize, Jest, package.json)
- Seed data guidance was vague in Iter 1 ("サンプルデータを含める"). Iter 2 explicitly says "idempotent startup seed with existence check" -- this was directly followed
- `data-testid` was mentioned in Iter 1 skill too, but this is the first scenario where it applies (web app). The instruction worked correctly.

**Remaining gaps**:
- No guidance on session management approach (cookie-based, JWT, etc.) -- had to choose express-session independently
- No guidance on view engine choice when `app_type=web` -- EJS was specified in custom_requirements but the skill doesn't mention template engines
- No guidance on authentication patterns (session vs token) -- this was left to AI judgment

---

### Phase 3: Test Generation and Execution

**Clarity**: 4.5/5 (improved from 4/5)
**Completeness**: 4.5/5 (improved from 4/5)
**Correctness**: 5/5 (unchanged)

**Observations**:
- The instruction to use in-memory SQLite for tests (added in Iter 2 skill improvements) was directly applicable: `NODE_ENV=test` triggers `:memory:` storage
- Unit tests cover models (User password hashing/validation, Project defaults, Ticket associations, seed idempotency)
- Integration tests cover all routes including auth flow, protected route redirection, ticket CRUD, status/assignment updates, project listing, 404 handling
- `supertest` agent with session persistence correctly tests authenticated flows
- All 35 tests passed on first run with zero self-correction loops needed

**What improved from Iter 1**:
- Iter 1 noted "Missing: No mention of test database isolation strategy". Iter 2 skill now says "テスト用DBはインメモリSQLiteを使用し、テストごとにリセットする" -- this was directly followed
- The explicit test framework guidance (Jest for Node.js) removed ambiguity

---

### Phase 4: Build Configuration

**Clarity**: 5/5 (improved from 5/5 -- already good, now better)
**Completeness**: 5/5 (improved from 4/5)
**Correctness**: 5/5 (improved from 4/5)

**Observations**:
- **Non-root user**: Skill now explicitly says "ランタイムステージでは非rootユーザーで実行してください" -- implemented with `adduser -D appuser` + `USER appuser`
- **.dockerignore**: Skill now explicitly lists files to exclude -- generated correctly with `node_modules/`, `tests/`, `*.test.*`, `database.sqlite`
- **Dockerfile CMD consistency**: Skill says "CMD のモジュールパスはDockerfile内のWORKDIRとソースコピー先に合わせてください" -- `WORKDIR /app` + `COPY . .` + `CMD ["node", "app.js"]` is consistent
- **Multi-stage build**: Builder stage installs production deps only, runtime stage copies only what's needed
- **HEALTHCHECK**: Uses `wget` (alpine-compatible) to check `/health` endpoint

**What improved from Iter 1**:
- Iter 1 had no .dockerignore at all. Iter 2 skill explicitly requires it -- generated correctly
- Iter 1 had no non-root user guidance. Iter 2 skill explicitly requires it -- implemented correctly
- Iter 1 had CMD path confusion (app.main vs main). Iter 2 skill's explicit guidance about WORKDIR+COPY+CMD consistency prevented this entirely

---

## Improvement Impact Assessment

### Improvements that HELPED (directly from Iter 1 feedback -> Iter 2 skill changes)

| Improvement | Impact | Evidence |
|---|---|---|
| Language/FW guidance table | HIGH | Immediately directed to Sequelize/Jest/Express structure without guesswork |
| DB local development strategy table | HIGH | SQLite fallback for MySQL was clear and worked perfectly |
| Seed data idempotent startup guidance | HIGH | Implemented exact pattern: count check before insert |
| .dockerignore requirement | MEDIUM | Generated without needing to invent what to exclude |
| Non-root user in Dockerfile | MEDIUM | `adduser -D appuser` + `USER appuser` directly from guidance |
| CMD path consistency guidance | MEDIUM | No path confusion; WORKDIR/COPY/CMD aligned correctly |
| In-memory SQLite for tests | MEDIUM | Test isolation worked cleanly |

### Improvements that were NOT TESTED in this scenario

| Improvement | Reason |
|---|---|
| FastAPI lifespan vs on_event | Python-specific, not applicable to Node.js |
| SQLAlchemy guidance | Python-specific |
| conftest.py patterns | Python-specific |

### NEW issues discovered in Iteration 2 (not seen in Iter 1)

| Issue | Severity | Description |
|---|---|---|
| No authentication pattern guidance | LOW | Skill doesn't specify session vs JWT vs basic auth for web apps. Had to choose express-session independently. |
| No view/template engine guidance | LOW | For `app_type=web`, no guidance on what template engine to use. EJS was in custom_requirements here, but a generic web app request wouldn't have this. |
| No session store guidance | LOW | For container deployments, in-memory sessions won't work across replicas. Skill should mention this consideration. |
| `additional_services` not used | LOW | "logging" was specified but the skill has no guidance on how to implement logging integration. This field is ignored. |
| No guidance on static file serving | LOW | Web apps need CSS/JS. The skill doesn't mention `public/` directory or static file middleware. |
| connect-session-sequelize sync | VERY LOW | Session store `sync()` is called but could fail silently. Minor issue for demo quality. |

---

## Overall Skill Assessment (Iteration 2)

| Dimension | Iter 1 Score | Iter 2 Score | Delta | Notes |
|---|---|---|---|---|
| **Clarity** | 4.25/5 | 4.5/5 | +0.25 | Tables and explicit guidance reduced ambiguity |
| **Completeness** | 3.5/5 | 4.25/5 | +0.75 | DB strategy, .dockerignore, non-root user, seed guidance all filled gaps |
| **Correctness** | 4.25/5 | 4.75/5 | +0.50 | CMD path consistency, test DB isolation guidance prevented errors |
| **Overall** | **4.0/5** | **4.5/5** | **+0.50** | Significant improvement; generates working code with less AI guesswork |

---

## Generated File Inventory

```
generated/ticket-system-demo/app/
  app.js                  # Express app with session auth, EJS, /health
  package.json            # Dependencies (express, sequelize, ejs, bcryptjs, jest)
  Dockerfile              # Multi-stage build, non-root user, HEALTHCHECK
  .dockerignore           # Excludes node_modules, tests, sqlite db
  middleware/
    auth.js               # Session-based authentication middleware
  models/
    index.js              # Sequelize init with SQLite fallback, associations
    user.js               # User model with bcrypt password hashing
    project.js            # Project model
    ticket.js             # Ticket model with status/priority validation
    seed.js               # Idempotent seed data (3 users, 2 projects, 5 tickets)
  routes/
    auth.js               # Login/logout routes
    tickets.js            # Ticket CRUD, status update, assignment
    projects.js           # Project listing with ticket counts
  views/
    error.ejs
    partials/
      header.ejs          # Nav with data-testid attributes
      footer.ejs
    auth/
      login.ejs           # Login form with data-testid attributes
    tickets/
      index.ejs           # Ticket list table
      new.ejs             # New ticket form
      show.ejs            # Ticket detail with status/assign forms
    projects/
      index.ejs           # Project list
      show.ejs            # Project detail with tickets
  public/
    css/
      style.css           # Complete stylesheet
  tests/
    setup.js              # Shared test setup (not used, inline setup preferred)
    models.test.js        # 11 unit tests (User, Project, Ticket, seed idempotency)
    api.test.js           # 24 integration tests (health, auth, tickets, projects)
```

---

## Top Priority Improvements for Iteration 3

1. **Add web app specific guidance**: For `app_type=web`, include guidance on:
   - Template engine selection (EJS, Pug, Handlebars, or framework equivalent)
   - Static file directory structure (`public/css/`, `public/js/`)
   - Authentication pattern (session-based for SSR, JWT for SPA)

2. **Map `additional_services` to code patterns**: Currently `logging`, `monitoring`, etc. are ignored. Add a table mapping these to concrete implementations (e.g., `logging` -> winston/morgan for Node.js, logging module for Python).

3. **Add guidance for `compute_new_or_existing` and `network` fields**: These hearing result fields are not referenced by the skill at all. At minimum, note that they are for infrastructure generation and can be ignored by app generation.

4. **Test the serverless path**: `app_type=serverless` and `app_type=batch` have not been tested. The `func.yaml` generation and batch entry point patterns need validation.

5. **Consider multi-replica session strategy**: For container deployments, note that in-memory sessions won't persist across replicas. Suggest using DB-backed session store (already done in this implementation, but not guided by skill).
