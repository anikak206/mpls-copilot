# 11. Normalization Analysis (3NF)

## 1NF
Every column holds a single atomic value (no lists or repeating groups). Telemetry metrics are separate typed columns; each sample is its own row. Every table has a primary key.

## 2NF
All primary keys are single-column surrogate keys, so no partial dependency on part of a composite key is possible.

## 3NF — no transitive dependencies
| Design decision | Why it satisfies 3NF |
|---|---|
| `roles` separated from `users` | Role description depends on role, not on user. Users hold only `role_id`. |
| `sites` separated from `devices` | Region/address depend on site, not device. |
| `predictions` reference `telemetry_id` only (no `device_id`) | Device is reached through telemetry; storing it again would be transitive. Ad-hoc feature input is first stored as a telemetry row in the same transaction. |
| `recommendations` 1:1 with prediction (`prediction_id` UNIQUE) | Recommendation attributes depend only on the recommendation key. |
| `outcomes` 1:1 with action (`action_id` UNIQUE) | Outcome is a separate fact recorded later, by possibly another user. |
| Names/emails are not copied into operational tables | Reports obtain them by JOIN (`users`, `devices`, `sites`). |

## Deliberate, documented exceptions
| Column | Reason |
|---|---|
| `alerts.device_id` alongside nullable `alerts.telemetry_id` | Manual alerts have no telemetry row; the device is the alert's own subject. For trigger/ML alerts, `device_id` equals the telemetry's device — enforced by the trigger/service that create them. |
| `engineer_actions.device_id` alongside nullable `recommendation_id` / `incident_id` | Actions can exist without any recommendation or incident; the device acted on is a fact of the action itself. The API rejects links whose device does not match (HTTP 422). |
| `audit_logs.entity_type/entity_id` (polymorphic reference) | An append-only log must survive deletion of the referenced row, so no FK is used by design. |

Derived values (counts, averages, latest risk) are **not stored**; they are computed by views (`v_device_health`, `v_prediction_report`), aggregate queries and `sp_device_risk_summary`.

Result: the schema is in **Third Normal Form**, with the three listed deviations justified by business semantics rather than redundancy for convenience.
