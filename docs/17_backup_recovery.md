# 17. Backup and Recovery

## Backup (mysqldump)
```bash
mysqldump -h 127.0.0.1 -u mpls_app -p --single-transaction --routines --triggers --events \
  mpls_copilot > backups/mpls_copilot_$(date +%Y%m%d_%H%M%S).sql
# or: bash scripts/backup.sh
```
`--routines --triggers` are required so stored procedures and triggers are included; `--single-transaction` gives a consistent InnoDB snapshot without locking.

## Restore (mysql)
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS mpls_copilot_restore CHARACTER SET utf8mb4;"
mysql -h 127.0.0.1 -u mpls_app -p mpls_copilot_restore < backups/mpls_copilot_YYYYMMDD_HHMMSS.sql
# or: bash scripts/backup.sh restore backups/<file>.sql   (restores into MYSQL_DATABASE)
```

## Docker
```bash
docker compose exec db mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --routines --triggers mpls_copilot > backup.sql
docker compose exec -T db mysql -u root -p"$MYSQL_ROOT_PASSWORD" mpls_copilot < backup.sql
```

## Verified in this environment
`scripts/backup.sh` produced a 112 KB dump of the development database; it was restored into the disposable `mpls_copilot_test` database and checked: 576 telemetry rows, 36 predictions, 5 triggers, 2 procedures (see `docs/test-results/backup_restore_check.txt`).

## Recommended policy (template)
- Daily full dump retained 14 days; weekly retained 8 weeks; copy to offline/air-gapped storage.
- Monthly restore drill into a scratch database.
- Protect dump files: they contain password hashes and operational data.
