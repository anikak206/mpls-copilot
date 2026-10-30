#!/usr/bin/env bash
# Development helper: installs (if missing) and starts a local MariaDB server,
# then creates the application database and user from backend/.env values.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATADIR="$ROOT/.mysql_data"
set -a; source "$ROOT/backend/.env"; set +a

if ! command -v mariadbd >/dev/null 2>&1; then
  DEBIAN_FRONTEND=noninteractive apt-get install -y mariadb-server mariadb-client
fi
mkdir -p "$DATADIR" /run/mysqld && chown -R mysql:mysql "$DATADIR" /run/mysqld
if [ ! -d "$DATADIR/mysql" ]; then
  mariadb-install-db --user=mysql --datadir="$DATADIR" >/dev/null
fi
if ! mysqladmin --socket=/run/mysqld/mysqld.sock ping --silent 2>/dev/null; then
  (mysqld_safe --user=mysql --datadir="$DATADIR" --bind-address=127.0.0.1 --port="$MYSQL_PORT" >/tmp/mysqld.log 2>&1 &)
  for _ in $(seq 1 30); do mysqladmin --socket=/run/mysqld/mysqld.sock ping --silent 2>/dev/null && break; sleep 1; done
fi
mariadb --protocol=socket -uroot -p"$MYSQL_ROOT_PASSWORD" --socket=/run/mysqld/mysqld.sock <<SQL
CREATE DATABASE IF NOT EXISTS \`$MYSQL_DATABASE\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}_test\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
CREATE USER IF NOT EXISTS '$MYSQL_USER'@'127.0.0.1' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON \`$MYSQL_DATABASE\`.* TO '$MYSQL_USER'@'localhost', '$MYSQL_USER'@'127.0.0.1';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}_test\`.* TO '$MYSQL_USER'@'localhost', '$MYSQL_USER'@'127.0.0.1';
SET GLOBAL log_bin_trust_function_creators = 1;
FLUSH PRIVILEGES;
SQL
echo "MariaDB ready on 127.0.0.1:$MYSQL_PORT (db=$MYSQL_DATABASE)"
