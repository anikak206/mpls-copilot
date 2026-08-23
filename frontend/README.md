# Dashboard Frontend (Person 2, Phase 8)

Not started yet — this is a placeholder so the repo structure is ready.

## When you start Phase 8
- Recommended: React + a charting library (Recharts or Chart.js) to match
  device health, alerts, risk scores, predictions, explanations, and trends
  from the plan's dashboard requirements.
- Point it at the backend's documented API (`http://localhost:8000/docs`)
  rather than guessing endpoint shapes — Person 1 keeps that documentation
  current as routers in `backend/app/routers/` get filled in.
- Respect RBAC in the UI too: hide admin-only views from `network_engineer`
  and `viewer` roles, even though the backend already enforces this — the
  UI check is for usability, the API check is what actually secures it.
