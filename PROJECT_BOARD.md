# Project Board — Task Breakdown

Assumption baked into this split: **Person 1 is the stronger SQL/backend person**, so
Person 1 owns the database and backend more heavily than a strict 50-50, and Person 2
gets correspondingly more of the AI/ML and frontend surface. Joint items stay joint —
don't let those quietly become one person's job.

## Phase 3 — Backend & APIs (Week 3-5)

**Person 1 (lead, ~70%)**
- [ ] DB connectivity layer (`backend/app/core/database.py`) against `database/schema.sql`
- [ ] Auth: login endpoint issuing JWT (`backend/app/routers/auth.py`)
- [ ] RBAC dependency enforcing admin / network_engineer / viewer (`backend/app/core/deps.py`)
- [ ] CRUD endpoints: devices, telemetry, alerts, incidents
- [ ] CRUD endpoints: predictions, recommendations, actions, outcomes, reports
- [ ] Input validation + structured error handling
- [ ] OpenAPI docs reviewed and shared with Person 2

**Person 2 (support, ~30%)**
- [ ] Agree on API request/response JSON shapes with Person 1 *before* endpoints are built
- [ ] Write a Postman/pytest smoke-test collection against the agreed contract
- [ ] Start Phase 4 data prep early against the schema (doesn't need the live API)

**Sync point:** API contract frozen — Person 2 can point real requests at it instead of mocks.

## Phase 4 — Data Preparation (Week 5-6)
**Person 2 (solo)** — clean/structure network data, feature engineering, train/val/test split.
**Person 1** — Phase 3 hardening + start audit-trail wiring into every write endpoint.

## Phase 5 — AI/ML Engine (Week 6-9)
**Person 2 (lead)** — anomaly detection baseline → failure-prediction model → train/evaluate → package for offline inference.
**Person 1 (support)** — build the endpoints that will serve predictions; harden security (least-privilege DB accounts, session expiry, encryption at rest).

## Phase 6 — Risk & Explainability (Week 9-10)
**Person 2 (lead)** — risk tiers, SHAP/feature-importance explanations.
**Person 1 (support)** — storage/retrieval for `contributing_factors` (already JSON in schema), expose via API.

## Phase 7 — Recommendation & Feedback (Week 10-11)
**Person 2** — rules engine mapping risk factors → recommendations.
**Person 1** — engineer-action + outcome endpoints (tables already exist), wire feedback loop into audit log.

## Phase 8 — Dashboard (Week 11-13)
**Person 2 (lead, solo build)** — dashboard views, charts, RBAC-aware UI.
**Person 1 (support)** — make sure every API the dashboard needs is documented/fast/correctly scoped; start Phase 9 backend test-writing in parallel.

## Phase 9 — Integration & Testing (Week 13-15)
- Person 1: backend/API tests, security tests (auth bypass, injection, RBAC), load testing
- Person 2: model performance validation, end-to-end workflow through the dashboard
- **Both together:** full end-to-end run in the air-gapped staging environment

## Phase 10 — Documentation & Patent Study (Week 15-16)
- Person 1 writes: architecture, database design, API reference, security model
- Person 2 writes: AI/ML methodology, evaluation results, dashboard walkthrough
- **Both:** prior-art search, final report/PPT assembly

## Always Joint (whole project)
- Feedback Mechanism
- System Architecture
- Testing / Documentation
- Patent / Prior-Art Research
