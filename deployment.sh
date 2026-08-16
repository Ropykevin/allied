#!/usr/bin/env bash
# Allied Tours & Travel — deployment helper
# Usage:
#   ./deployment.sh check
#   ./deployment.sh build
#   ./deployment.sh up
#   ./deployment.sh migrate
#   ./deployment.sh seed          # optional; roles + content (demo users gated)
#   ./deployment.sh down
#   ./deployment.sh logs
#   ./deployment.sh status
#   ./deployment.sh restart
#   ./deployment.sh deploy        # check → build → up → migrate

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

COMPOSE=(docker compose)
WEB_SERVICE="${WEB_SERVICE:-web}"
DB_SERVICE="${DB_SERVICE:-db}"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "'$1' is required but not installed."
}

load_env() {
  [[ -f .env ]] || die ".env missing. Copy .env.example → .env and set secrets."
  # shellcheck disable=SC1091
  set -a
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
      export "$line"
    fi
  done < .env
  set +a
}

check_env() {
  load_env
  local missing=()
  [[ -z "${SECRET_KEY:-}" || "$SECRET_KEY" == "change-me-to-a-long-random-string" ]] && missing+=("SECRET_KEY")
  [[ ${#SECRET_KEY:-0} -lt 32 ]] && missing+=("SECRET_KEY(>=32 chars)")
  [[ -z "${POSTGRES_PASSWORD:-}" || "$POSTGRES_PASSWORD" == "REPLACE_WITH_STRONG_PASSWORD" ]] && missing+=("POSTGRES_PASSWORD")
  [[ -z "${FLASK_ENV:-}" ]] && export FLASK_ENV=production

  if ((${#missing[@]})); then
    die "Fix these .env values before deploy: ${missing[*]}"
  fi

  if [[ ! -f Dockerfile ]]; then
    die "Dockerfile not found in $ROOT_DIR"
  fi
  if [[ ! -f docker-compose.yml ]]; then
    die "docker-compose.yml not found in $ROOT_DIR"
  fi

  log "Environment looks ready (FLASK_ENV=${FLASK_ENV})"
}

cmd_check() {
  require_cmd docker
  docker compose version >/dev/null || die "Docker Compose plugin is required."
  check_env
  log "Files present: Dockerfile, docker-compose.yml, mypsql.sh, deployment.sh"
  ls -la Dockerfile docker-compose.yml mypsql.sh deployment.sh
}

cmd_build() {
  require_cmd docker
  check_env
  log "Building images..."
  "${COMPOSE[@]}" build --pull
}

cmd_up() {
  require_cmd docker
  check_env
  log "Starting services..."
  "${COMPOSE[@]}" up -d --remove-orphans
  log "Waiting for database..."
  local i=0
  until "${COMPOSE[@]}" exec -T "$DB_SERVICE" pg_isready -U "${POSTGRES_USER:-allied}" -d "${POSTGRES_DB:-allied_tours}" >/dev/null 2>&1; do
    i=$((i + 1))
    (( i > 60 )) && die "Database did not become ready in time."
    sleep 2
  done
  log "Stack is up. App: http://localhost:${WEB_PORT:-8000}"
}

cmd_migrate() {
  require_cmd docker
  load_env
  log "Running database migrations..."
  "${COMPOSE[@]}" exec -T "$WEB_SERVICE" flask db upgrade
  log "Migrations complete."
}

cmd_seed() {
  require_cmd docker
  load_env
  log "Seeding roles/permissions/content (demo users only if SEED_DEMO_USERS=true)..."
  "${COMPOSE[@]}" exec -T \
    -e SEED_DEMO_USERS="${SEED_DEMO_USERS:-false}" \
    -e SEED_ADMIN_EMAIL="${SEED_ADMIN_EMAIL:-}" \
    -e SEED_ADMIN_PASSWORD="${SEED_ADMIN_PASSWORD:-}" \
    "$WEB_SERVICE" flask seed
  log "Seed complete."
}

cmd_down() {
  require_cmd docker
  log "Stopping services..."
  "${COMPOSE[@]}" down
}

cmd_logs() {
  require_cmd docker
  "${COMPOSE[@]}" logs -f --tail=200 "$@"
}

cmd_status() {
  require_cmd docker
  "${COMPOSE[@]}" ps
  if [[ -x ./mypsql.sh ]]; then
    ./mypsql.sh status || true
  fi
}

cmd_restart() {
  require_cmd docker
  load_env
  log "Restarting web..."
  "${COMPOSE[@]}" restart "$WEB_SERVICE"
}

cmd_deploy() {
  cmd_check
  cmd_build
  cmd_up
  # migrate also runs on container start; run again to be explicit/idempotent
  cmd_migrate
  log "Deploy finished."
  log "Admin: http://localhost:${WEB_PORT:-8000}/admin/login"
  log "Tip: create first Super Admin with SEED_ADMIN_EMAIL/PASSWORD then: ./deployment.sh seed"
}

usage() {
  cat <<EOF
Allied Tours & Travel — deployment

Usage: ./deployment.sh <command>

Commands:
  check      Verify Docker, .env secrets, and required files
  build      Build Docker images
  up         Start db + web (detached)
  migrate    Run flask db upgrade inside web
  seed       Run flask seed (gated demo users)
  down       Stop stack
  logs       Follow container logs
  status     Show compose status + DB readiness
  restart    Restart web service
  deploy     check → build → up → migrate

Examples:
  cp .env.example .env   # then set SECRET_KEY + POSTGRES_PASSWORD
  ./deployment.sh deploy
  ./mypsql.sh backup
EOF
}

main() {
  local cmd="${1:-}"
  shift || true
  case "$cmd" in
    check) check_env; cmd_check ;;
    build) cmd_build ;;
    up) cmd_up ;;
    migrate) cmd_migrate ;;
    seed) cmd_seed ;;
    down) cmd_down ;;
    logs) cmd_logs "$@" ;;
    status) cmd_status ;;
    restart) cmd_restart ;;
    deploy) cmd_deploy ;;
    ""|-h|--help|help) usage ;;
    *) die "Unknown command: $cmd (try ./deployment.sh help)" ;;
  esac
}

main "$@"
