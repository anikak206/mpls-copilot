# Contributing (Team of 2)

## Commit messages
Use a short prefix so history is scannable:
- `db:` schema/migration changes
- `api:` backend endpoint work
- `ai:` model/data-prep work
- `ui:` dashboard work
- `docs:` documentation
- `test:` tests
- `fix:` bug fixes

Example: `api: add RBAC-protected CRUD for devices`

## Before opening a PR
- [ ] Code runs locally (`uvicorn app.main:app --reload` for backend changes)
- [ ] `pytest` passes in `backend/`
- [ ] No `.env`, credentials, or raw telemetry data committed
- [ ] PR description says which Phase / task from `PROJECT_BOARD.md` this covers

## Review
The other person reviews every PR before merge, even for small changes — this
is what gives you a visible two-person review trail for your faculty, and
catches schema/API-contract drift early since you're working in different
folders most of the time.
