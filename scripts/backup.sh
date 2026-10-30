#!/usr/bin/env bash
# Usage: scripts/backup.sh            -> backups/mpls_copilot_<timestamp>.sql
#        scripts/backup.sh restore FILE
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a; source "$ROOT/backend/.env"; set +a
mkdir -p "$ROOT/backups"
DUMP=$(command -v mysqldump || command -v mariadb-dump)
CLIENT=$(command -v mysql || command -v mariadb)
if [ "${1:-}" = "restore" ]; then
  "$CLIENT" -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < "$2"
  echo "Restored $2 into $MYSQL_DATABASE"
else
  OUT="$ROOT/backups/${MYSQL_DATABASE}_$(date +%Y%m%d_%H%M%S).sql"
  "$DUMP" -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
    --single-transaction --routines --triggers --events "$MYSQL_DATABASE" > "$OUT"
  echo "Backup written to $OUT"
fi
