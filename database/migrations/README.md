# Migrations

For now, `schema.sql` in the parent folder is the single source of truth (run once
to set up a fresh database). Once the schema needs to change after Phase 3 starts,
add numbered migration files here instead of editing `schema.sql` directly, e.g.:

```
001_add_metric_unit_default.sql
002_add_devices_last_seen_column.sql
```

This keeps the change history visible in git and avoids breaking a teammate's
already-running local database.
