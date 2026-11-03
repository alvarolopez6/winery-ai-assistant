#!/usr/bin/env bash
#
# Back up PostgreSQL, the demo documents and n8n state to a Restic repository.
# Credentials are read from an env file, never from this script.
#
# Required environment (or a file sourced via BACKUP_ENV_FILE):
#   RESTIC_REPOSITORY
#   RESTIC_PASSWORD
#   B2_ACCOUNT_ID       (only for Backblaze B2)
#   B2_ACCOUNT_KEY      (only for Backblaze B2)

set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/winery-assistant}"
BACKUP_ENV_FILE="${BACKUP_ENV_FILE:-$HOME/.config/winery-assistant/backup.env}"
STOP_N8N="${BACKUP_STOP_N8N:-true}"
STAGING_RETENTION_DAYS="${BACKUP_STAGING_RETENTION_DAYS:-7}"

log() {
  printf '[%s] %s\n' "$(date -Is)" "$*"
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

if [[ -f "$BACKUP_ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$BACKUP_ENV_FILE"
fi

for command in docker restic; do
  command -v "$command" >/dev/null 2>&1 || die "$command is not installed"
done

: "${RESTIC_REPOSITORY:?set RESTIC_REPOSITORY}"
: "${RESTIC_PASSWORD:?set RESTIC_PASSWORD}"

mkdir -p "$BACKUP_DIR"
exec 9>"$BACKUP_DIR/.lock"
flock -n 9 || die "another backup is already running"

N8N_WAS_RUNNING=false
cleanup() {
  if [[ "$N8N_WAS_RUNNING" == "true" ]]; then
    log "starting n8n again"
    docker compose -f "$PROJECT_DIR/docker-compose.yml" start n8n >/dev/null || true
  fi
}
trap cleanup EXIT

log "dumping PostgreSQL"
pg_tmp="$(mktemp "$BACKUP_DIR/postgres.XXXXXX.sql")"
docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-winery}" "${POSTGRES_DB:-winery}" >"$pg_tmp"
mv "$pg_tmp" "$BACKUP_DIR/postgres.sql"

log "syncing demo documents"
mkdir -p "$BACKUP_DIR/documents"
rsync -a --delete "$PROJECT_DIR/examples/" "$BACKUP_DIR/documents/"

log "copying n8n state"
mkdir -p "$BACKUP_DIR/n8n"
if [[ "$STOP_N8N" == "true" ]]; then
  if docker compose -f "$PROJECT_DIR/docker-compose.yml" ps --status running --services | grep -qx n8n; then
    N8N_WAS_RUNNING=true
    docker compose -f "$PROJECT_DIR/docker-compose.yml" stop n8n >/dev/null
  fi
fi
docker compose -f "$PROJECT_DIR/docker-compose.yml" cp n8n:/home/node/.n8n/. "$BACKUP_DIR/n8n/" >/dev/null

log "running Restic"
restic backup \
  --tag winery-assistant \
  --exclude '.lock' \
  --exclude '*.tmp' \
  "$BACKUP_DIR"

log "applying retention policy"
restic forget \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 12 \
  --prune

log "removing staging files older than ${STAGING_RETENTION_DAYS} days"
find "$BACKUP_DIR" -type f -mtime "+${STAGING_RETENTION_DAYS}" -delete

log "backup completed"
