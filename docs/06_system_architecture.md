# 6. System Architecture

```
 Browser (React SPA)                       FastAPI backend (port 8001)                    MySQL / MariaDB
 ┌─────────────────────┐  HTTPS + Bearer  ┌───────────────────────────────┐  SQLAlchemy  ┌──────────────────────┐
 │ Login, Dashboard,   │ ───────────────▶ │ routers/ (auth, users,        │ ───────────▶ │ 13 tables (3NF)      │
 │ Devices, Telemetry, │   /api/*  JSON   │  devices, telemetry,          │  PyMySQL     │ 2 views              │
 │ Alerts, Incidents,  │ ◀─────────────── │  incidents, predictions,      │              │ 2 stored procedures  │
 │ Predictions, Recs,  │                  │  actions, reports, db-lab)    │ ◀─────────── │ 5 triggers           │
 │ Actions, Reports,   │                  │ security.py  JWT + RBAC +     │              └──────────────────────┘
 │ DB Lab, Audit, Users│                  │              engineer scoping │
 └─────────────────────┘                  │ prediction_service.py ──────┐ │
                                          └─────────────────────────────┼─┘
                                                                        ▼
                                          ml/ (local, no network): preprocessing → IsolationForest
                                          (ml/models/anomaly_model.joblib) → risk calibration →
                                          explanation (z-scores) → recommender (advisory playbook)
```

## Backend modules
| Module | Responsibility |
|---|---|
| `app/config.py` | Loads required settings from `backend/.env`; fails fast if missing |
| `app/database.py` | Engine, session factory, declarative base |
| `app/models.py` | 13 ORM models with PK/FK/UNIQUE/CHECK/DEFAULT and indexes |
| `app/schemas.py` | Pydantic request validation (ranges, enums, IP, email) |
| `app/security.py` | bcrypt, JWT issue/verify, revocation check, `require_roles`, engineer device scoping |
| `app/utils.py` | Pagination, audit logging helper |
| `app/prediction_service.py` | Prediction + recommendation + ML alert inside caller's transaction |
| `app/reports.py`, `app/exporters.py` | Parameterized report SQL on views/procedure; CSV/PDF export |
| `app/routers/*` | REST endpoints grouped by resource |
| `app/bootstrap.py`, `app/seed.py` | Alembic upgrade, model check, idempotent dev seed |
| `alembic/` | Migration `0001_baseline` (tables + views + procedures + triggers) |

## Request flow example — "Run prediction"
1. Engineer submits features → `POST /api/predictions/run` with Bearer token.
2. `require_roles(Administrator, Network Engineer)` + device-assignment check.
3. One SQLAlchemy transaction: insert telemetry (trigger may add a threshold alert) → local inference → insert prediction → insert recommendation → insert ML alert if anomalous → audit row → COMMIT (ROLLBACK on any exception).

## Air-gap guarantees
- ML inference is a local scikit-learn call; there is no outbound HTTP client in the backend.
- Fonts are bundled via `@fontsource` packages (no CDN at runtime in the production build).
- Note: the development preview page includes the hosting platform's preview script; the packaged `frontend/public/index.html` in the ZIP does not.
