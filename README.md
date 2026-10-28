# Air-Gapped Predictive Copilot for Secure MPLS Operations

A secure, locally deployable network-management application. It stores MPLS operational data in MySQL, detects abnormal telemetry with a **local** machine-learning model, estimates risk, recommends preventive action and records what engineers did, with role-based access for Administrators, Network Engineers and Auditors. No external AI API is used at runtime.

## Features
- JWT login/logout (token revocation), bcrypt hashing, brute-force lockout, backend-enforced RBAC (engineers see only assigned devices)
- Dashboard: device status, active alerts, incidents, risk distribution, 48 h telemetry trends, recent activity
- Devices (CRUD, search, filters, pagination), Telemetry (history, filters, validated manual entry)
- Alerts (from MySQL trigger, ML or manual; acknowledge/resolve/escalate via stored procedure), Incidents (status workflow, trigger-recorded history)
- Predictions (local IsolationForest, explainable risk score, normal/uncertain/anomalous), Recommendations (advisory), Engineer actions & outcomes
- Reports (views, JOINs, stored procedure) with CSV and PDF export; append-only audit log; user & role management
- Database Lab page demonstrating JOIN, aggregate, view, procedure and transaction commit/rollback live

## Technology stack
React 19 (CRA, JavaScript) · FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic · MySQL 8 / MariaDB 10.11 · PyJWT · bcrypt · pandas · NumPy · scikit-learn · reportlab · pytest · Jest · Docker Compose · GitHub Actions.
Deviation from the preferred stack: the frontend uses Create React App with JavaScript instead of Vite + TypeScript because the development environment's managed dev server runs CRA (see `docs/01_project_proposal.md`).

## Project structure
```
backend/            FastAPI app (app/ models, schemas, security, routers), alembic/ migrations, server.py
frontend/           React app (src/pages, src/components, src/lib, src/context)
database/           schema.sql, views.sql, procedures.sql, triggers.sql, seed.sql
ml/                 data/ (generator), preprocessing/, training/ (train, evaluate, train_unsw), inference/, models/
tests/backend/      pytest suite (runs against a disposable <db>_test database)
docs/               proposal, architecture, ER diagrams, schema, dictionary, 3NF, DB features, security,
                    backup, ML model card, test results, compliance matrix (MD + PDF)
scripts/            start_mysql.sh (local MariaDB helper), backup.sh (backup/restore), package.sh
.github/workflows/  ci.yml
```

## 1. Prerequisites
Python 3.11+, Node 20 + Yarn 1.x, MySQL 8 (or MariaDB ≥ 10.6). Or just Docker.

## 2. Configuration
```bash
cp .env.example backend/.env          # then edit every value
python -c "import secrets; print(secrets.token_hex(32))"   # use for JWT_SECRET
echo 'REACT_APP_BACKEND_URL="http://localhost:8001"' > frontend/.env
```

## 3. Database setup (MySQL)
```sql
CREATE DATABASE mpls_copilot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE mpls_copilot_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;   -- for tests
CREATE USER 'mpls_app'@'localhost' IDENTIFIED BY '<MYSQL_PASSWORD>';
GRANT ALL PRIVILEGES ON mpls_copilot.* TO 'mpls_app'@'localhost';
GRANT ALL PRIVILEGES ON mpls_copilot_test.* TO 'mpls_app'@'localhost';
SET GLOBAL log_bin_trust_function_creators = 1;   -- MySQL 8 with binary logging: allows triggers/procedures
```
Tables, views, procedures and triggers are created by **Alembic** automatically when the backend starts (`alembic upgrade head`). Manual alternative:
`mysql mpls_copilot < database/schema.sql && mysql mpls_copilot < database/views.sql && mysql mpls_copilot < database/procedures.sql && mysql mpls_copilot < database/seed.sql && mysql mpls_copilot < database/triggers.sql`
(MariaDB on Debian/Ubuntu: `bash scripts/start_mysql.sh` installs/starts a local server using backend/.env values.)

## 4. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.docker.txt
python -m ml.training.train   # optional: (re)train model — run from project root: cd .. && python -m ml.training.train
uvicorn server:app --host 0.0.0.0 --port 8001
```
On startup the app runs migrations, ensures the ML artifact exists (trains it if missing) and seeds development data once.
API docs (OpenAPI/Swagger): http://localhost:8001/api/docs · ReDoc: /api/redoc · JSON: /api/openapi.json

## 5. Frontend
```bash
cd frontend && yarn install && yarn start      # http://localhost:3000
yarn build                                      # production bundle in frontend/build
```

## 6. Demo users (development only)
Seeded from `backend/.env`: `ADMIN_EMAIL/ADMIN_PASSWORD` (Administrator), `ENGINEER_EMAIL/ENGINEER_PASSWORD` (Network Engineer; also `engineer2@mpls.local` with the same password), `AUDITOR_EMAIL/AUDITOR_PASSWORD` (Auditor). Changing a password in `.env` and restarting updates the hash. Leave blank to skip. Never use these in production.

## 7. Docker
```bash
cp .env.example backend/.env && edit it ; export $(grep -v '^#' backend/.env | xargs)
docker compose up --build       # db:3306, backend:8001, frontend:3000
```

## 8. Tests
```bash
python -m pytest tests/backend -v        # uses <MYSQL_DATABASE>_test, rebuilt each run; never touches the main DB
cd frontend && CI=true yarn test --watchAll=false
python -m ml.training.evaluate           # recomputes ml/models/metrics.json
```
Latest results: `docs/18_testing_results.md`.

## 9. Backup & restore
`bash scripts/backup.sh` · `bash scripts/backup.sh restore backups/<file>.sql` — details in `docs/17_backup_recovery.md`.

## 10. GitHub setup and branch workflow
```bash
git init && git add . && git commit -m "Initial project import"
git branch -M main && git remote add origin https://github.com/<your-account>/<repo>.git && git push -u origin main
git checkout -b dev && git push -u origin dev
```
- `main`: stable, demo-ready; only updated by pull requests from `dev`.
- `dev`: integration branch; features are developed in `feature/<name>` branches and merged into `dev` via PR after CI passes.
- Commit progressively (one logical change per commit). `.github/workflows/ci.yml` runs pytest against MySQL and the frontend build on pushes/PRs to `main` and `dev`.
No repository, commits or collaborators have been created for you — do this yourself so the history is genuine.

## 11. Deployment guide (not performed)
1. Provision a VM (or managed MySQL + container host) inside your network.
2. Set production `backend/.env` (strong secrets, `CORS_ORIGINS` = your domain).
3. `docker compose up -d --build`; put a TLS reverse proxy (nginx/Caddy) in front of ports 3000/8001.
4. Push images to Docker Hub: `docker tag <img> <user>/mpls-copilot-backend:1.0 && docker push ...` (not done).
5. Schedule `scripts/backup.sh` (cron) and test restores.
No live deployment, Docker Hub image or custom domain has been created or verified.

## Documentation index
See `docs/` — files are numbered to match the faculty documentation list; `docs/20_compliance_matrix.pdf` maps every rubric item to evidence.
