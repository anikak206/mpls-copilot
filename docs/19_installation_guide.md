# 19. Installation and Execution Guide

The exact, step-by-step instructions are in the project **README.md** (sections 1–9):

1. Prerequisites → 2. Configuration (`backend/.env`, `frontend/.env`) → 3. MySQL database & user → 4. Backend (`uvicorn server:app --port 8001`, migrations + seed automatic) → 5. Frontend (`yarn start`) → 6. Demo users → 7. Docker Compose → 8. Tests → 9. Backup/restore.

Quick start (Docker):
```bash
cp .env.example backend/.env   # edit values
export $(grep -v '^#' backend/.env | xargs)
docker compose up --build
# open http://localhost:3000 ; API docs http://localhost:8001/api/docs
```

Troubleshooting
| Symptom | Fix |
|---|---|
| `Missing required environment variable` | Fill every key from `.env.example` into `backend/.env` |
| `1419 You do not have the SUPER privilege` when creating triggers | `SET GLOBAL log_bin_trust_function_creators = 1;` (MySQL with binary logging) |
| Login returns 429 | 5 failed attempts in 15 min; wait or use another account |
| Predictions show `mode: demo` | `ml/models/anomaly_model.joblib` missing — run `python -m ml.training.train` from the project root |
