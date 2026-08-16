#!/bin/sh
# Entrypoint: build a safe DATABASE_URL (URL-encodes password) then run CMD.
set -eu

DB_USER="${POSTGRES_USER:-allied}"
DB_PASS="${POSTGRES_PASSWORD:-}"
DB_NAME="${POSTGRES_DB:-allied_tours}"
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"

if [ -n "$DB_PASS" ]; then
  # Encode password so characters like @ : / # do not break the URL.
  ENCODED_PASS="$(python -c "import os,urllib.parse; print(urllib.parse.quote_plus(os.environ['POSTGRES_PASSWORD']))")"
  export DATABASE_URL="postgresql+psycopg2://${DB_USER}:${ENCODED_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
fi

exec "$@"
