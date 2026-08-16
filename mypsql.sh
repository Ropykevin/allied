#!/usr/bin/env bash
# Allied Tours & Travel — PostgreSQL helper
# Usage:
#   ./mypsql.sh shell          Interactive psql
#   ./mypsql.sh status         Database readiness
#   ./mypsql.sh backup         Dump to ./backups/
#   ./mypsql.sh restore FILE   Restore from dump
#   ./mypsql.sh create-user    Create role/db if missing (local/docker network)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a
  # Export only simple KEY=VALUE lines (skip comments / blanks)
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
      export "$line"
    fi
  done < .env
  set +a
fi

POSTGRES_DB="${POSTGRES_DB:-allied_tours}"
POSTGRES_USER="${POSTGRES_USER:-allied}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
COMPOSE_DB_SERVICE="${COMPOSE_DB_SERVICE:-db}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"

use_compose_exec() {
  command -v docker >/dev/null 2>&1 \
    && docker compose ps --status running --services 2>/dev/null | grep -qx "$COMPOSE_DB_SERVICE"
}

psql_cmd() {
  if use_compose_exec; then
    docker compose exec -T \
      -e PGPASSWORD="$POSTGRES_PASSWORD" \
      "$COMPOSE_DB_SERVICE" \
      psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" "$@"
  else
    if [[ -z "$POSTGRES_PASSWORD" ]]; then
      echo "ERROR: POSTGRES_PASSWORD is not set in .env" >&2
      exit 1
    fi
    PGPASSWORD="$POSTGRES_PASSWORD" psql \
      -h "$POSTGRES_HOST" \
      -p "$POSTGRES_PORT" \
      -U "$POSTGRES_USER" \
      -d "$POSTGRES_DB" \
      "$@"
  fi
}

pg_dump_cmd() {
  local outfile="$1"
  mkdir -p "$BACKUP_DIR"
  if use_compose_exec; then
    docker compose exec -T \
      -e PGPASSWORD="$POSTGRES_PASSWORD" \
      "$COMPOSE_DB_SERVICE" \
      pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --format=custom \
      > "$outfile"
  else
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
      -h "$POSTGRES_HOST" \
      -p "$POSTGRES_PORT" \
      -U "$POSTGRES_USER" \
      -d "$POSTGRES_DB" \
      --no-owner --format=custom \
      -f "$outfile"
  fi
}

cmd="${1:-shell}"
shift || true

case "$cmd" in
  shell|psql)
    echo "Connecting to ${POSTGRES_USER}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB} ..."
    if use_compose_exec; then
      docker compose exec \
        -e PGPASSWORD="$POSTGRES_PASSWORD" \
        "$COMPOSE_DB_SERVICE" \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
    else
      PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB"
    fi
    ;;

  status)
    if use_compose_exec; then
      docker compose exec -T "$COMPOSE_DB_SERVICE" \
        pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
    else
      PGPASSWORD="$POSTGRES_PASSWORD" pg_isready \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB"
    fi
    echo "OK — database is accepting connections."
    ;;

  backup)
    ts="$(date +%Y%m%d_%H%M%S)"
    outfile="${BACKUP_DIR}/allied_${POSTGRES_DB}_${ts}.dump"
    echo "Backing up to $outfile ..."
    pg_dump_cmd "$outfile"
    echo "Backup complete: $outfile"
    ;;

  restore)
    file="${1:-}"
    if [[ -z "$file" || ! -f "$file" ]]; then
      echo "Usage: ./mypsql.sh restore path/to/backup.dump" >&2
      exit 1
    fi
    echo "WARNING: This will overwrite database '$POSTGRES_DB'."
    read -r -p "Type YES to continue: " confirm
    [[ "$confirm" == "YES" ]] || { echo "Aborted."; exit 1; }

    if use_compose_exec; then
      cat "$file" | docker compose exec -T \
        -e PGPASSWORD="$POSTGRES_PASSWORD" \
        "$COMPOSE_DB_SERVICE" \
        pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner
    else
      PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --clean --if-exists --no-owner \
        "$file"
    fi
    echo "Restore complete."
    ;;

  create-user)
    if [[ -z "$POSTGRES_PASSWORD" ]]; then
      echo "ERROR: Set POSTGRES_PASSWORD in .env first." >&2
      exit 1
    fi
    if use_compose_exec; then
      echo "Compose Postgres already creates the role/db from env. Nothing to do."
      exit 0
    fi
    echo "Creating role/database on ${POSTGRES_HOST} (requires local superuser access)..."
    sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
    CREATE ROLE ${POSTGRES_USER} LOGIN PASSWORD '${POSTGRES_PASSWORD}';
  END IF;
END
\$\$;
SELECT 'CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}')\gexec
GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};
SQL
    echo "Done."
    ;;

  *)
    cat <<EOF
Usage: ./mypsql.sh <command>

Commands:
  shell        Open interactive psql (compose exec if db container is up)
  status       Check database readiness
  backup       Create a custom-format dump in ./backups/
  restore FILE Restore a dump (destructive — asks for YES)
  create-user  Create local role/database (non-compose hosts)

Env (from .env): POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
                 POSTGRES_HOST, POSTGRES_PORT
EOF
    exit 1
    ;;
esac
