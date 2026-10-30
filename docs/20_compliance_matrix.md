# 20. Faculty Rubric Compliance Matrix

Generated 2026-10-31. Marks are an evidence-based **estimate**; items only described in documentation are not awarded.

| Category | Max | Estimated |
|---|---|---|
| 1. Problem Statement & Project Planning | 2 | 2 |
| 2. Database Design | 6 | 6 |
| 3. Database Implementation | 8 | 8 |
| 4. Application Development | 4 | 4 |
| 5. Authentication, Authorization & Database Security | 5 | 5 |
| 6. Professional Development Practices | 5 | 2.5 |
| **Total** | **30** | **28.0** |

## 1. Problem Statement & Project Planning — 2/2

| Requirement | Implementation | Location | Test | Result | Status | Missing work |
|---|---|---|---|---|---|---|
| Project title, problem statement, objectives, scope | Written proposal | docs/01_project_proposal.md | Inspected | Present | PASS | — |
| Team members & responsibilities | Aarohi Verma (24BDS0438) & Anika K (24BCE0245) with roles | docs/01_project_proposal.md | Inspected | Present | PASS | – |
| Technology stack & deliverables | Table incl. documented CRA deviation | docs/01_project_proposal.md | Inspected | Present | PASS | — |
| Gantt chart | Mermaid gantt + week table (template dates) | docs/01_project_proposal.md | Inspected | Present | PASS | Adjust dates to semester |

## 2. Database Design — 6/6

| Requirement | Implementation | Location | Test | Result | Status | Missing work |
|---|---|---|---|---|---|---|
| ER diagram | Generated from ORM metadata: detailed + presentation (PNG/SVG/PDF) + Mermaid | docs/er/ | Generator run; 13 tables / 24 FKs | Matches schema | PASS | — |
| Min. 4 primary entities | 13 tables | backend/app/models.py, database/schema.sql | pytest test_connection_and_tables | Passed | PASS | — |
| Min. 3 relationships | 24 foreign keys (1:N, 1:1) | docs/07_08_er_diagrams.md | pytest test_foreign_keys_and_indexes | Passed | PASS | — |
| Relational schema | Generated from metadata | docs/09_relational_schema.md | Inspected | Present | PASS | — |
| Keys & constraints (PK, FK, UNIQUE, CHECK, NOT NULL, DEFAULT) | 23 CHECK constraints, UNIQUE keys, FK actions | database/schema.sql | pytest constraint tests | Passed | PASS | — |
| Normalization 3NF | Analysis with justified exceptions | docs/11_normalization_3nf.md | Inspected | Present | PASS | — |
| Data dictionary (recommended) | Generated per table | docs/10_data_dictionary.md | Inspected | Present | PASS | — |

## 3. Database Implementation — 8/8

| Requirement | Implementation | Location | Test | Result | Status | Missing work |
|---|---|---|---|---|---|---|
| Database creation & table design | Alembic 0001_baseline + schema.sql | backend/alembic, database/schema.sql | pytest schema tests | Passed | PASS | — |
| CRUD | ORM create/read/update/delete via API | backend/app/routers/devices.py etc. | pytest test_device_crud_and_validation | Passed | PASS | — |
| JOIN queries | Reports, Database Lab, ORM joins | app/routers/dblab.py, app/reports.py | pytest test_join_and_aggregate_queries | Passed | PASS | — |
| Views | v_device_health, v_prediction_report | database/views.sql | pytest test_views_return_rows | Passed | PASS | — |
| Aggregate queries | Dashboard GROUP BY, DB Lab, procedure | app/routers/reports.py | pytest + E2E dashboard | Passed | PASS | — |
| Transactions (commit & rollback) | Prediction workflow, actions, transaction demo, procedure | app/routers/predictions.py, dblab.py | pytest test_transaction_demo_rollback_and_commit | Passed | PASS | — |
| Stored procedure / trigger | 2 procedures, 5 triggers | database/procedures.sql, triggers.sql | pytest procedure + trigger tests | Passed | PASS | — |
| ORM integration | SQLAlchemy 2 for all app access | backend/app/ | pytest API tests persist to MySQL | Passed | PASS | — |

## 4. Application Development — 4/4

| Requirement | Implementation | Location | Test | Result | Status | Missing work |
|---|---|---|---|---|---|---|
| Framework-based application | FastAPI + React | backend/, frontend/ | Build + E2E | Passed | PASS | — |
| Dashboard | Stats, charts, recent activity | frontend/src/pages/Dashboard.js | E2E | Passed | PASS | — |
| Search / filtering / pagination | All list pages | frontend/src/pages/* | pytest test_pagination + E2E | Passed | PASS | — |
| Validation | Pydantic + frontend validators + DB CHECK | app/schemas.py, src/lib/validation.js | pytest + Jest 4 tests | Passed | PASS | — |
| Exception handling | Mapped 401/403/404/409/422/429/500 | backend/server.py | pytest | Passed | PASS | — |
| Responsive UI | CSS breakpoints 1100/860 px | frontend/src/App.css | E2E 390 px + screenshots | Passed after fix | PASS | — |

## 5. Authentication, Authorization & Database Security — 5/5

| Requirement | Implementation | Location | Test | Result | Status | Missing work |
|---|---|---|---|---|---|---|
| JWT authentication | Login, me, logout with revocation, expiry | app/routers/auth.py, app/security.py | pytest auth tests + E2E | Passed | PASS | — |
| RBAC using single Users table | users + roles; require_roles on every endpoint; engineer scoping | app/security.py | pytest test_rbac_forbidden_actions | Passed | PASS | — |
| ORM-based authorization | scope_to_assigned() filters SQLAlchemy queries | app/security.py | pytest test_engineer_sees_only_assigned_devices | Passed | PASS | — |
| Password hashing | bcrypt cost 12 | app/security.py | pytest test_password_is_bcrypt_hashed | Passed | PASS | — |
| SQL injection prevention | ORM + bound parameters, whitelisted filters | app/reports.py | Code inspection | No string-built user SQL | PASS | — |
| Secrets management | .env + .env.example + .gitignore | backend/.env (excluded), .env.example | Inspected ZIP | No secrets packaged | PASS | — |

## 6. Professional Development Practices — 2.5/5

| Requirement | Implementation | Location | Test | Result | Status | Missing work |
|---|---|---|---|---|---|---|
| GitHub: progressive commits & branching | Documented main/dev workflow | README.md §10 | — | No repository exists | NOT VERIFIABLE | Create repo; commit progressively; create dev branch |
| .gitignore | Excludes .env, venvs, node_modules, DB data | .gitignore | Inspected | Present | PASS | — |
| Database backup & restore | scripts/backup.sh, guide | docs/17_backup_recovery.md | Dump + restore into test DB | Passed | PASS | — |
| Docker | docker-compose.yml, 2 Dockerfiles | docker-compose.yml | Not executed (no Docker in env) | Unverified | PARTIAL | Run docker compose up and record evidence |
| Docker Hub | Instructions only | README.md §11 | — | Not done | MISSING | Push images to Docker Hub |
| Cloud deployment (live URL) | Guide only | README.md §11 | — | Not deployed | MISSING | Deploy with a MySQL-capable host and record URL |

## Bonus opportunities (assessed separately)

| Bonus | Implementation | Location | Status | Estimate |
|---|---|---|---|---|
| CI/CD pipeline (GitHub Actions) | Workflow written (pytest on MySQL + frontend build) | .github/workflows/ci.yml | PARTIAL — not run | +0 until it runs green on GitHub |
| Custom domain | None | — | MISSING | +0 |
| Additional best practice: automated testing + append-only audit logging | 37 pytest + 4 Jest + E2E; trigger-enforced audit | tests/, database/triggers.sql | PASS | +1 |

Estimated bonus: **+1** (verified automated testing and audit logging).

Marks impact: the main deductions are in Professional Practices (no verified GitHub history, Docker run, Docker Hub or cloud deployment) and Planning (team placeholders).
