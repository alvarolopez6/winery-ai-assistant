# Operations

## Backup architecture

Backups are **off-site in the cloud**, not only on the machine that runs the
stack:

```text
PostgreSQL dump ─┐
Demo documents  ─┼──> staging directory ──> Restic ──> Backblaze B2 (cloud)
n8n state       ─┘
```

The Restic repository is a Backblaze B2 bucket, accessed through Restic's
native B2 backend. The staging directory is local and temporary; the durable
copy is the encrypted one in the cloud.

`scripts/backup.sh` performs:

1. `pg_dump` against the running PostgreSQL container.
2. `rsync` of `examples/` (the knowledge base).
3. A copy of the n8n volume, stopping n8n first by default to avoid a
   half-written SQLite file.
4. `restic backup`.
5. `restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune`.
6. Cleanup of staging files older than seven days.

## Credentials

Create `~/.config/winery-assistant/backup.env` with permissions `600`:

```bash
export RESTIC_REPOSITORY="b2:<bucket>:/restic"
export RESTIC_PASSWORD="..."
export B2_ACCOUNT_ID="..."
export B2_ACCOUNT_KEY="..."
```

The script sources this file. It never reads secrets from the repository.

## Running a backup

```bash
./scripts/backup.sh
```

Useful overrides:

| Variable | Default | Purpose |
|---|---|---|
| `BACKUP_DIR` | `~/backups/winery-assistant` | Local staging directory |
| `BACKUP_ENV_FILE` | `~/.config/winery-assistant/backup.env` | Credentials file |
| `BACKUP_STOP_N8N` | `true` | Stop n8n before copying SQLite |
| `BACKUP_STAGING_RETENTION_DAYS` | `7` | Delete old staging files |

## Automation

`scripts/backup.sh` is currently run **manually**. Automatic scheduling is a
pending item for a simple reason: the demo runs on a local machine that is not
powered on permanently. A cron job or systemd timer on that machine would fire
only while it is awake, so a missed window would look identical to a healthy
backup unless it alerted.

Automating backups makes sense once the stack moves to an always-on host (VPS,
a home server left running, or a scheduled CI job with B2 credentials). The
automation should include a dead-man's-switch alert when no snapshot arrives
within the expected window. Tracked in [`ROADMAP.md`](ROADMAP.md).

## Restore

1. Stop the stack:

   ```bash
   docker compose down
   ```

2. Restore the Restic snapshot into a temporary directory:

   ```bash
   restic restore latest --target /tmp/restore
   ```

3. Restore PostgreSQL:

   ```bash
   docker compose up -d postgres
   docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB" \
     < /tmp/restore/postgres.sql
   ```

4. Restore n8n state:

   ```bash
   docker compose up -d n8n
   docker compose cp /tmp/restore/n8n/. n8n:/home/node/.n8n/
   docker compose restart n8n
   ```

5. Rebuild Qdrant from the documents:

   ```bash
   python scripts/rag_ingest.py --source examples/demo --recreate
   ```

   Qdrant embeddings are derived data; rebuilding them is safer than restoring a
   stale vector snapshot.

6. Verify:

   - n8n loads the workflows.
   - Credentials decrypt (the encryption key must match).
   - A test query returns a grounded answer.
   - A test conversation changes state correctly.

## Monitoring

- `docker compose ps` shows container health.
- `docker compose logs -f --tail=100` follows logs.
- The gateway exposes `/healthz`; it returns 503 when the app secret or verify token is missing.
- n8n exposes `/healthz` on the private network.
- Add an external uptime check for the public gateway URL.
- Alert on failed backups and on Instagram token expiry.

## Upgrades

1. Read the release notes for n8n, Qdrant and PostgreSQL.
2. Change one image tag at a time in `docker-compose.yml`.
3. Run `docker compose pull` and `docker compose up -d`.
4. Re-run the smoke test.
5. Keep the previous tag available for rollback.

Do not use `latest` in production. The Compose file pins versions on purpose.

## Incident response

1. Rotate the affected credential.
2. Revoke the Meta or Telegram token at the provider.
3. Check n8n execution history for leaked headers.
4. Restore from the last known-good backup if data was modified.
5. Document the incident and the rotation in the repository's security notes.
