# 7–8. ER Diagrams

All diagrams are **generated from the SQLAlchemy metadata** by `docs/er/generate_er.py`, which is the same metadata Alembic uses to create the database. They therefore contain exactly the 13 implemented tables and 24 foreign-key relationships.

| File | Purpose |
|---|---|
| `er/er_diagram_detailed.png` / `.svg` / `.pdf` | Detailed ER: every column, type, PK/FK/UQ/NN markers, cardinality on each relationship |
| `er/er_diagram_presentation.png` / `.svg` / `.pdf` | Presentation ER: entities and labelled relationships only |
| `er/er_diagram.mmd` | Editable Mermaid `erDiagram` source (paste into mermaid.live or a Markdown viewer) |

Regenerate after any schema change: `python docs/er/generate_er.py`

## Entities (13)
roles, users, revoked_tokens, sites, devices, telemetry, predictions, recommendations, alerts, incidents, engineer_actions, outcomes, audit_logs.

## Key relationships
| Parent → Child | Cardinality | FK (on delete) |
|---|---|---|
| roles → users | 1 : N | users.role_id (RESTRICT) |
| users → revoked_tokens | 1 : N | user_id (CASCADE) |
| sites → devices | 1 : N | devices.site_id (RESTRICT) |
| users → devices | 1 : N optional (assigned engineer) | assigned_engineer_id (SET NULL) |
| devices → telemetry | 1 : N | telemetry.device_id (CASCADE) |
| telemetry → predictions | 1 : N | predictions.telemetry_id (CASCADE) |
| predictions → recommendations | 1 : 1 | recommendations.prediction_id UNIQUE (CASCADE) |
| devices → alerts / incidents / engineer_actions | 1 : N | device_id (CASCADE) |
| telemetry / predictions / incidents → alerts | 1 : N optional | SET NULL |
| recommendations / incidents → engineer_actions | 1 : N optional | SET NULL |
| engineer_actions → outcomes | 1 : 1 | outcomes.action_id UNIQUE (CASCADE) |
| users → audit_logs, incidents, predictions, outcomes, telemetry, alerts | 1 : N optional | SET NULL |
| users → engineer_actions | 1 : N | engineer_id (RESTRICT) |
