# 18. Testing Results

All results below were produced in the development environment (MariaDB 10.11.19, Python 3.11, Node 20) on the dates shown in the raw output files. Nothing here is estimated.

## Summary
| Suite | Command | Result | Raw output |
|---|---|---|---|
| Backend + DB + ML (pytest, disposable `mpls_copilot_test` DB) | `python -m pytest tests/backend -v` | **37 passed, 0 failed** | `test-results/pytest-output.txt`, `pytest-junit.xml` |
| Frontend unit (Jest) | `CI=true yarn test --watchAll=false` | **4 passed, 0 failed** | `test-results/jest-output.txt` |
| Frontend production build | `yarn build` | **Compiled successfully** | `test-results/frontend-build.txt` |
| End-to-end UI (Playwright, automated QA run on preview URL, 3 roles, desktop + 390 px) | — | All main flows passed; 2 layout bugs found | `test-results/e2e_iteration_1.json` |
| ML evaluation | `python -m ml.training.evaluate` | ROC-AUC 0.9928, F1 0.7681 (synthetic) | `../ml/models/metrics.json` |
| Backup → restore | `scripts/backup.sh` + `mysql < dump` into test DB | Row counts, 5 triggers, 2 procedures restored | `test-results/backup_restore_check.txt` |
| Index usage | `EXPLAIN` on per-device 24 h telemetry query | Uses `ix_telemetry_device_time` (range) | `test-results/explain_index.txt` |

## pytest coverage by requirement
| Area | Tests |
|---|---|
| DB connection & schema, Alembic version | `test_connection_and_tables` |
| FKs, indexes | `test_foreign_keys_and_indexes` |
| CHECK, UNIQUE, FK constraints | `test_check_constraint_rejects_out_of_range`, `test_unique_and_fk_constraints` |
| Views | `test_views_return_rows` |
| Stored procedures (+ input validation, commit/rollback) | `test_procedure_risk_summary`, `test_procedure_escalation_commit_and_rollback` |
| Triggers (derived alert, closed_at, audit, append-only) | `test_trigger_raises_alert_on_threshold_breach`, `test_incident_triggers_audit_and_closed_at`, `test_audit_logs_are_append_only`, `test_incident_update_audited_by_trigger` |
| Transactions | `test_transaction_demo_rollback_and_commit` |
| JOIN & aggregate queries | `test_join_and_aggregate_queries` |
| Authentication, hashing, logout revocation, lockout | `test_login_invalid_and_me`, `test_password_is_bcrypt_hashed`, `test_logout_revokes_token`, `test_bruteforce_lockout` |
| RBAC & engineer scoping | `test_rbac_forbidden_actions`, `test_engineer_sees_only_assigned_devices` |
| CRUD, validation, pagination, error codes | `test_device_crud_and_validation`, `test_pagination`, `test_telemetry_validation_and_trigger_alert`, `test_user_management` |
| ML inference + persistence + recommendations | `test_prediction_workflow_persists`, `test_ml.py` (10 tests) |
| Engineer actions & outcomes | `test_engineer_action_and_outcome` |
| Reports CSV/PDF | `test_reports_and_exports` |
| Audit logging | `test_audit_logging_of_sensitive_operations` |

## Issues found and fixed
| Found by | Issue | Fix | Re-verified |
|---|---|---|---|
| pytest | `days=0` accepted by risk-summary report | explicit `None` check → 422 | pytest re-run, passed |
| E2E QA | Modals confined to content area; close button covered by top bar | Modal rendered via React portal; animation fill-mode `backwards` | Screenshot: close button clickable |
| E2E QA | Database Lab overflowed horizontally at 390 px | `.grid > * { min-width: 0 }` | Screenshot: scrollWidth = 390 |
| E2E QA | Toasts covered Sign-out; user status shown as up/down; outcome form allowed empty result; deactivate had no confirmation; chart hours in UTC | Toasts bottom-right; Active/Disabled; required select; confirm dialog; local-time axis | Visual check |

## Not executed / blocked
| Item | Status | Reason |
|---|---|---|
| Docker Compose build/run | Not executed | Docker is not available in the development container; files inspected only |
| GitHub Actions CI | Not executed | No GitHub repository exists yet; workflow inspected only |
| MySQL 8.x (exact) | Not executed | Verified on MariaDB 10.11 (MySQL-compatible); Docker file targets mysql:8.4 |
| UNSW-NB15 training | Not executed | Dataset not available offline |
| Full E2E re-run after UI fixes | Not executed | Fixes verified by targeted screenshots only |
