#!/usr/bin/env bash
#
# Export the current schema without owners or privileges.
# Useful for reviewing changes before adding a migration.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT="${1:-$PROJECT_DIR/sql/schema.sql}"

command -v docker >/dev/null 2>&1 || {
  printf 'error: docker is not installed\n' >&2
  exit 1
}

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T postgres \
  pg_dump \
  -U "${POSTGRES_USER:-winery}" \
  --schema-only \
  --no-owner \
  --no-privileges \
  "${POSTGRES_DB:-winery}" >"$tmp"

mv "$tmp" "$OUTPUT"
printf 'schema written to %s\n' "$OUTPUT"
