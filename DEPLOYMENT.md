# Deployment guide

The app is three pieces:

| Piece | What it needs | Suggested host (free tier) |
|---|---|---|
| **MySQL 8** | Stored procedures, triggers, views → needs `CREATE ROUTINE` / `TRIGGER` | Aiven for MySQL (free plan) |
| **Backend** (FastAPI, `backend/Dockerfile`) | Docker, env vars, `/api/health` | Render → Web Service (Docker, free) |
| **Frontend** (React/CRA, `frontend/`) | Static build with `REACT_APP_BACKEND_URL` baked in | Vercel (free) |

The backend bootstraps itself on start: it runs the Alembic baseline (tables + views + procedures + triggers),
trains the ML model if `ml/models/anomaly_model.joblib` is missing, and seeds demo users. No manual SQL import is needed.

> PlanetScale / TiDB Cloud will **not** work: the baseline migration creates stored procedures and triggers,
> which those engines reject.

---

## Option A — free stack (Render + Aiven + Vercel)

### 1. MySQL on Aiven
1. Create an Aiven account → **Create service** → **MySQL** → plan **Free** → pick the region closest to you (e.g. `google-asia-southeast1`).
2. Wait for the service to be **Running**, open it and copy the **Service URI** (`mysql://avnadmin:...@host:port/defaultdb`).
3. Copy the CA certificate (`ca.pem`) if your plan shows one — the app accepts the connection without host verification, so it is optional.

### 2. Backend on Render
1. Render → **New** → **Blueprint** → connect `anikak206/mpls-copilot`. It reads `render.yaml` and creates `mpls-copilot-api`.
2. Fill the prompted env vars (`sync: false` ones):

| Key | Value |
|---|---|
| `MYSQL_HOST` | host from the Aiven URI |
| `MYSQL_PORT` | port from the Aiven URI (usually `10000`+) |
| `MYSQL_USER` | `avnadmin` |
| `MYSQL_PASSWORD` | password from the Aiven URI |
| `MYSQL_DATABASE` | `defaultdb` (or a DB you created) |
| `MYSQL_SSL` | `1` (already set in `render.yaml`) |
| `CORS_ORIGINS` | your Vercel URL, e.g. `https://mpls-copilot.vercel.app` |
| `ADMIN_PASSWORD` / `ENGINEER_PASSWORD` / `AUDITOR_PASSWORD` | strong demo passwords |

3. Deploy. First boot takes a few minutes (it trains the ML model). Check `https://<service>.onrender.com/api/health` → `{"status":"ok",...}`.

> Free Render services sleep after ~15 min idle; the first request afterwards takes ~50 s.

### 3. Frontend on Vercel
1. Vercel → **Add New Project** → import the repo.
2. **Root Directory**: `frontend` (Framework preset: Create React App — `frontend/vercel.json` overrides the build command).
3. Environment variable (Production + Preview): `REACT_APP_BACKEND_URL=https://<service>.onrender.com`
4. Deploy, then go back to Render and set `CORS_ORIGINS` to the final Vercel domain and redeploy.

> `REACT_APP_*` is baked in at build time — changing it requires a Vercel redeploy, not just a restart.

---

## Option B — one project on Railway (~$5 trial credit)

1. Railway → **New Project** → **Deploy from GitHub repo** → `anikak206/mpls-copilot`.
2. Add a **MySQL** database from the project canvas.
3. Create a second service from the same repo, set its **Dockerfile path** to `backend/Dockerfile` and root to `/`.
4. Env vars: `MYSQL_HOST=${{MySQL.MYSQLHOST}}`, `MYSQL_PORT=${{MySQL.MYSQLPORT}}`, `MYSQL_USER=${{MySQL.MYSQLUSER}}`,
   `MYSQL_PASSWORD=${{MySQL.MYSQLPASSWORD}}`, `MYSQL_DATABASE=${{MySQL.MYSQLDATABASE}}`, `JWT_SECRET=<random hex>`,
   `JWT_EXPIRE_MINUTES=60`, `CORS_ORIGINS=https://<frontend-domain>`, plus the three demo user pairs.
   `MYSQL_SSL` can stay unset (private network is plaintext).
5. Frontend: new service from the same repo, root `frontend`, builder **Dockerfile** (`frontend/Dockerfile`),
   build arg `REACT_APP_BACKEND_URL=https://<backend-domain>`.

---

## Environment variables (backend)

| Key | Required | Notes |
|---|---|---|
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` | yes | |
| `MYSQL_SSL` | managed DBs | `1` enables TLS for Aiven/PlanetScale-style hosts |
| `JWT_SECRET` | yes | 64 hex chars: `python -c "import secrets;print(secrets.token_hex(32))"` |
| `JWT_EXPIRE_MINUTES` | yes | e.g. `60` |
| `CORS_ORIGINS` | yes | comma-separated exact origins, no trailing slash |
| `ADMIN_EMAIL`/`ADMIN_PASSWORD` | no | demo seed users; leave blank to skip |
| `ENGINEER_EMAIL`/`ENGINEER_PASSWORD` | no | |
| `AUDITOR_EMAIL`/`AUDITOR_PASSWORD` | no | |

## Post-deploy checklist

- [ ] `GET /api/health` returns `{"status":"ok"}`
- [ ] `GET /api/docs` renders Swagger
- [ ] Login works from the deployed frontend (CORS is the usual culprit)
- [ ] Devices / incidents / predictions pages load data
- [ ] `ADMIN_PASSWORD` etc. are not the defaults from `.env.example`
