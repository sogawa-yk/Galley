# Final Quality Test: Node.js/Express + Container Instances + MySQL + LB + Auth

**Scenario**: Iteration 2 - CI deployment with MySQL, Load Balancer, session-based auth
**Date**: 2026-03-17

## Results

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | hearing: Container question asked for CI (not auto-skipped)? | PASS | hearing.md Phase 2 line 74-76: "コンピュート種別が Functions 以外（Compute/OKE/Container Instances）の場合、コンテナ化方式の質問は必ず提示する" |
| 2 | hearing: load_balancer defaults correctly for lb_public access? | PASS | hearing.md Phase 5 line 189-190: `access_type: "lb_public"` -> `load_balancer: true`, others -> `load_balancer: false` |
| 3 | generate-terraform: MySQL database template uses var.db_sizing? | PASS | database-template.md line 95: `shape_name = local.mysql_sizing[var.db_sizing].shape_name` |
| 4 | generate-terraform: MySQL outputs include db_host, db_port, db_user, db_connection_string? | PASS | outputs-template.md lines 121-146: db_host (ip_address), db_port, db_user (var.mysql_admin_username), db_connection_string (mysql:// format) |
| 5 | generate-terraform: LB generated for CI + load_balancer? | PASS | generate-terraform.md line 195: "compute_type: container_instances または compute_type: compute の場合のみTerraform管理のLBを生成" + lb.tf generated when load_balancer=true |
| 6 | generate-terraform: database-template display_name uses var.db_name (not project_name)? | PASS | database-template.md line 94: `display_name = var.db_name` with comment referencing database.name from result.json |
| 7 | generate-app: Node.js/Express guidance (Sequelize, Jest, package.json)? | PASS | generate-app.md line 69: Node.js/Express row specifies Sequelize/Prisma ORM, Jest test FW, package.json dependency management |
| 8 | generate-app: auth pattern (session-based for web)? | PASS | generate-app.md line 72: "Web app (app_type=web): セッションベース認証（express-session/Flask-Login）" |
| 9 | generate-app: seed-credentials.json output mandated? | PASS | generate-app.md lines 48-52: explicit instruction to output `seed-credentials.json` with username/password |
| 10 | generate-app: EJS template engine guidance? | PASS | generate-app.md line 77: "Node.js/Express: EJSをデフォルト使用、views/ディレクトリにテンプレート配置" |
| 11 | deploy-app: Phase 3.5 MySQL branch (host/port/user/password)? | PASS | deploy-app.md lines 129-175: MySQL branch sets DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME individually |
| 12 | deploy-app: NODE_ENV=production for Node.js? | PASS | deploy-app.md line 139: "Node.js: `NODE_ENV: \"production\"` を追加" in language-specific env vars |
| 13 | deploy-app: CI env_vars passed (deployer.py has environment_variables param)? | PASS | deployer.py line 152: `environment_variables: dict | None = None` param; line 173: passed into container spec as `environmentVariables` |
| 14 | deploy-app: LB endpoint resolution (lb_public_ip takes priority over CI IP)? | PASS | deploy-app.md lines 317-326: Priority order is 1) API Gateway URL, 2) LB Public IP, 3) direct compute IP |
| 15 | deploy-app: Phase 6 npm run seed for Node.js? | PASS | deploy-app.md lines 353-354: Seed command table shows Node.js -> `npm run seed` |
| 16 | verify: reads seed-credentials.json for auth tests? | PASS | verify.md lines 93-96: reads `generated/{project_name}/app/seed-credentials.json` for username/password |
| 17 | verify: session support in run_test_suite? | PASS | e2e_runner.py run_test_suite line 144: extracts `session` from spec and passes to check_endpoint; verify.md lines 113-114 documents session handling approach |
| 18 | e2e_runner: check_endpoint accepts session param? | PASS | e2e_runner.py line 69: `session: requests.Session | None = None` parameter; line 86: `requester = session if session is not None else requests` |

## Summary

**18 / 18 PASS** -- All checks passed. No failures found.

All skills and source files are consistent for the Node.js/Express + Container Instances + MySQL + LB + Auth scenario.
