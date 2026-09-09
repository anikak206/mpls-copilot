# Air-Gapped Predictive Copilot for Secure MPLS Operations

AI-assisted network operations system for air-gapped MPLS environments: continuous
telemetry monitoring, anomaly/failure prediction, explainable risk scoring, preventive
recommendations, and a full prediction → action → outcome → audit feedback loop.

## Team & Ownership

| Area | Owner | Support |
|---|---|---|
| Database, Backend, APIs, Auth/RBAC, Security | **Person 1** (SQL-strong) | Person 2 |
| AI/ML, Data Prep, Risk/Explainability, Frontend Dashboard | **Person 2** | Person 1 |
| Feedback loop, System architecture, Testing, Documentation | **Joint** | — |

See [`PROJECT_BOARD.md`](./PROJECT_BOARD.md) for the full phase-by-phase task breakdown.

## Repository Structure

```
mpls-copilot/
├── database/          # Schema, migrations, ER diagram — Person 1 owns this
│   └── schema.sql
├── backend/            # FastAPI backend, REST APIs, auth/RBAC — Person 1 owns this
│   └── app/
├── ai-engine/          # Data prep, anomaly detection, prediction models — Person 2 owns this
├── frontend/           # Dashboard (Phase 8) — Person 2 owns this
├── docs/                # Phase deliverables, architecture docs — joint
└── .github/workflows/   # CI — runs backend tests on every push/PR
```

Each top-level folder maps to one person's primary ownership so both of you can work
in parallel without stepping on each other's files — this is intentional and mirrors
the workload division in `PROJECT_BOARD.md`.

## Getting Started (Backend)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in your local MySQL credentials
mysql -u root -p < ../database/schema.sql
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` once running.

## Git Workflow 

1. **`main`** is always deployable/demo-ready. Never commit directly to it.
2. Create a branch per task: `feature/<phase>-<short-description>`, e.g.
   `feature/p3-devices-api`, `feature/p5-anomaly-model`.
3. Commit early and often with clear messages — faculty will likely check commit
   history as evidence of individual contribution, so **commit under your own name**
   (`git config user.name "Your Name"` locally) and avoid one person pushing all of
   the other's work.
4. Open a Pull Request into `main` when a task is done. The other person reviews
   and merges — this creates a visible review trail.
5. Tag a release (`v0.1-phase3`, `v0.2-phase5`, etc.) at the end of each phase so
   progress is easy to demonstrate.

### Suggested branch/PR cadence per phase
- Open the branch at the start of the phase.
- Push at least once a day you work on it (small commits > one giant commit).
- PR + merge at the phase's "sync point" described in `PROJECT_BOARD.md`.

## Setting Up the Remote

```bash
# after creating an empty repo on GitHub named e.g. "mpls-copilot"
git remote add origin https://github.com/<your-username>/mpls-copilot.git
git branch -M main
git push -u origin main
```

Then have your teammate `git clone` the same URL rather than starting a separate repo.

## Status

- [x] Phase 1 — Requirements & Architecture
- [x] Phase 2 — Database & Data Layer
- [x] Phase 3 — Backend & APIs 
- [ ] Phase 4 — Data Preparation
- [ ] Phase 5 — AI/ML Engine
- [ ] Phase 6 — Risk & Explainability
- [ ] Phase 7 — Recommendation & Feedback
- [ ] Phase 8 — Dashboard
- [ ] Phase 9 — Integration & Testing
- [ ] Phase 10 — Documentation & Patent Study
