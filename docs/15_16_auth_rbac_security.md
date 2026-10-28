# 15–16. Authentication, RBAC and Security Practices

## Authentication
- `POST /api/auth/login` — email + password; bcrypt (`$2b$`, cost 12) verification; returns a JWT (HS256) valid for `JWT_EXPIRE_MINUTES` (default 60) containing `sub`, `role`, `jti`, `iat`, `exp`, `type`.
- `GET /api/auth/me` — current user (password hash never returned).
- `POST /api/auth/logout` — inserts the token's `jti` into `revoked_tokens`; every request checks this table, so a logged-out token is rejected (401).
- Brute-force protection: 5 failed attempts per email within 15 minutes → HTTP 429 (counted from `audit_logs.login_failed`).
- Generic error message ("Invalid email or password") — no user enumeration.
- Frontend stores the token in `sessionStorage` (cleared when the tab closes) and drops it on any 401.

## Role-based access control (single `users` table + `roles`)
| Capability | Administrator | Network Engineer | Auditor |
|---|---|---|---|
| Users & roles | Full | — | — |
| Devices create/edit/delete, sites | Yes | — | — |
| View devices/telemetry/alerts/incidents/predictions/actions | All devices | **Assigned devices only** | All (read-only) |
| Record telemetry, run predictions | Yes | Assigned devices | — |
| Alerts ack/resolve/escalate, incidents create/update | Yes | Assigned devices | — |
| Delete incident | Yes | — | — |
| Engineer actions & outcomes | Yes | Assigned devices | Read |
| Reports & exports, Database Lab queries | Yes | Yes (scoped) | Yes |
| Transaction demo | Yes | — | — |
| Audit logs (read/export) | Yes | — | Yes |

Enforcement is on the backend: every router dependency uses `require_roles(...)` and `get_accessible_device(...)` / `scope_to_assigned(...)` (SQL `WHERE device_id IN (assigned devices)`). The frontend only mirrors this (role-based navigation and a forbidden page). Tested in `test_rbac_forbidden_actions` and `test_engineer_sees_only_assigned_devices`.

## Security practices
| Practice | Implementation |
|---|---|
| Secrets management | `backend/.env` (git-ignored); `.env.example` has placeholders only; settings fail fast if missing |
| Password hashing | bcrypt with per-password salt |
| SQL-injection prevention | ORM query building; raw SQL only via bound parameters (`text(... :param)`); no string concatenation of user input (report filter keys are whitelisted) |
| Input validation | Pydantic (`extra="forbid"`, ranges, enums, IP/email checks) + frontend form validation + DB CHECK constraints |
| Safe errors | DB errors mapped to generic 409/422/500 messages; stack traces never returned |
| CORS | Origins from `CORS_ORIGINS`; only required methods/headers |
| Token expiry & revocation | `exp` claim + `revoked_tokens` |
| Audit logging | Login success/failure, logout, user/device/site changes, telemetry, predictions, alerts, incidents (trigger), actions, outcomes, exports — append-only enforced by triggers |
| Least privilege DB user | App connects as `mpls_app` with privileges only on its own schemas |
| Data residency | No outbound calls to AI providers; ML runs locally |

Development demo accounts are seeded from `.env` values only (see README). Change all passwords and `JWT_SECRET` before any real use.
