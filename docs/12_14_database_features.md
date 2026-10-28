# 12–14. Database Implementation: Queries, CRUD, JOIN, Aggregates, Views, Transactions, Procedures, Triggers, Indexes

Files: `database/schema.sql`, `views.sql`, `procedures.sql`, `triggers.sql`, `seed.sql`; migration `backend/alembic/versions/0001_baseline.py`.
Live demonstration: **Database Lab** page (`/db-lab`) and `GET /api/db-lab/queries` execute every query below against MySQL and show the result rows.

## A. Database creation
```bash
mysql -u root -p -e "CREATE DATABASE mpls_copilot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
cd backend && alembic upgrade head          # or: mysql mpls_copilot < database/schema.sql (then views, procedures, seed, triggers)
```

## B. CRUD (through SQLAlchemy ORM, API)
| Operation | Endpoint | ORM / SQL effect |
|---|---|---|
| Create | `POST /api/devices` | `db.add(Device(...))` → INSERT |
| Read | `GET /api/devices?q=pe&status=up&page=1` | `select(Device).where(...).limit().offset()` |
| Update | `PATCH /api/devices/{id}` | attribute change → UPDATE |
| Delete | `DELETE /api/devices/{id}` | DELETE with FK CASCADE to telemetry/alerts/incidents |
Validation: Pydantic (types/ranges/enums), app checks (uniqueness → 409, foreign references → 422), DB CHECK/UNIQUE/FK constraints as the last line of defence. Tested in `tests/backend/test_api.py::test_device_crud_and_validation`.

## C. JOIN queries
```sql
-- Open alerts with device, site and linked incident
SELECT a.alert_id, d.hostname, s.name AS site, a.severity, a.status, i.title AS incident
FROM alerts a JOIN devices d ON d.device_id = a.device_id
JOIN sites s ON s.site_id = d.site_id
LEFT JOIN incidents i ON i.incident_id = a.incident_id
WHERE a.status <> 'resolved' ORDER BY a.created_at DESC LIMIT 10;

-- Predictions with telemetry, device and recommendation
SELECT p.prediction_id, d.hostname, t.recorded_at, p.label, p.risk_score, r.title
FROM predictions p JOIN telemetry t ON t.telemetry_id = p.telemetry_id
JOIN devices d ON d.device_id = t.device_id
LEFT JOIN recommendations r ON r.prediction_id = p.prediction_id
ORDER BY p.risk_score DESC LIMIT 10;

-- Engineer actions with outcome
SELECT ea.action_id, u.full_name, d.hostname, ea.action_type, o.result
FROM engineer_actions ea JOIN users u ON u.user_id = ea.engineer_id
JOIN devices d ON d.device_id = ea.device_id LEFT JOIN outcomes o ON o.action_id = ea.action_id;
```

## D. Aggregate queries
```sql
SELECT s.name, d.status, COUNT(*) FROM devices d JOIN sites s USING (site_id) GROUP BY s.name, d.status;
SELECT d.hostname, COUNT(*) samples, ROUND(AVG(t.cpu_util),2) avg_cpu, ROUND(AVG(t.latency_ms),2) avg_latency,
       ROUND(MAX(t.packet_loss_pct),3) max_loss
FROM telemetry t JOIN devices d USING (device_id) WHERE t.recorded_at >= NOW() - INTERVAL 1 DAY
GROUP BY d.hostname HAVING COUNT(*) > 0;
SELECT DATE(created_at) day, risk_level, COUNT(*), ROUND(AVG(risk_score),2) FROM predictions GROUP BY day, risk_level;
```
The dashboard (`GET /api/dashboard/summary`) uses ORM `GROUP BY` aggregates: devices by status, open alerts by severity, incidents by status, risk/label distribution, hourly telemetry averages.

## E. Views (`database/views.sql`)
- `v_device_health` — device + site + engineer + 24 h averages + open alerts + latest risk.
- `v_prediction_report` — prediction + telemetry + device + site + recommendation + requester.
Demo: `SELECT * FROM v_device_health ORDER BY latest_risk_score DESC;` — used by Reports → "Device health".

## F. Transactions
| Where | Statements in one transaction | Rollback evidence |
|---|---|---|
| `POST /api/predictions/run` | telemetry INSERT, prediction INSERT, recommendation INSERT, alert INSERT, audit INSERT | `except: db.rollback()` |
| `POST /api/actions` | action INSERT + optional outcome INSERT + audit | same |
| `POST /api/db-lab/transaction-demo` | incident + alert + audit; `simulate_failure=true` raises before COMMIT | returns identical before/after counts — `test_transaction_demo_rollback_and_commit` |
| `sp_open_incident_from_alert` | START TRANSACTION … COMMIT; EXIT HANDLER → ROLLBACK + RESIGNAL | second escalation of the same alert fails with no new incident — `test_procedure_escalation_commit_and_rollback` |

## G. Stored procedures (`database/procedures.sql`)
1. `sp_open_incident_from_alert(IN alert, IN user, OUT incident)` — atomic escalation (UI: Alerts → Escalate).
2. `sp_device_risk_summary(IN days)` — per-device prediction counts, anomalies, avg/max risk; validates input with SIGNAL.
```sql
CALL sp_open_incident_from_alert(1, 1, @inc); SELECT @inc;
CALL sp_device_risk_summary(7);
```

## H. Triggers (`database/triggers.sql`)
| Trigger | Event | Purpose |
|---|---|---|
| `trg_telemetry_threshold_alert` | AFTER INSERT telemetry | Derived record: creates a major/critical alert on hard threshold breach |
| `trg_incident_before_update` | BEFORE UPDATE incidents | Maintains `closed_at` |
| `trg_incident_status_audit` | AFTER UPDATE incidents | Writes one audit row per status change (actor from `@app_user_id`); the API does not log status changes itself → no duplicates |
| `trg_audit_logs_no_update` / `_no_delete` | BEFORE UPDATE/DELETE audit_logs | Append-only audit trail |
No trigger writes to its own table, so there is no recursion.

## I. Indexes
| Index | Supports |
|---|---|
| `ix_telemetry_device_time (device_id, recorded_at)` | Per-device history, 24 h averages (EXPLAIN shows `range` on this index, see `docs/test-results/explain_index.txt`) |
| `ix_telemetry_time` | Dashboard 48 h series |
| `ix_alerts_device_status`, `ix_alerts_created` | Open-alert counts per device, newest-first lists |
| `ix_incidents_status`, `ix_devices_status` | Status filters and dashboard grouping |
| `ix_predictions_telemetry`, `ix_predictions_created`, `ix_predictions_level` | Joins to telemetry, recent predictions, risk filter |
| `ix_audit_created`, `ix_audit_entity`, `ix_audit_action` | Audit filtering, incident history, brute-force lockout lookup |
| UNIQUE on users.email, devices.hostname, devices.mgmt_ip, roles.name, sites.name, recommendations.prediction_id, outcomes.action_id | Integrity + lookups |

## J. ORM
All application reads/writes use SQLAlchemy 2.0 (`select()`, `db.add`, relationships). Direct SQL is limited to: views/procedure/report queries (parameterized `text()` with bound parameters), the `SET @app_user_id` session variable for the audit trigger, and the stored-procedure call.
