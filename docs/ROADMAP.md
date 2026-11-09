# Roadmap

## Implemented

- Instagram DM webhook through a public FastAPI gateway.
- Meta GET verification and `X-Hub-Signature-256` validation.
- Tenant resolution by Instagram account.
- Per-tenant Qdrant retrieval.
- Structured DeepSeek answers with Gemini embeddings.
- Human handoff state machine.
- Telegram operator commands.
- Local RAG demo without Meta.
- Restic backup and restore runbook (manual; the demo host is not always on).
- CI, tests, sanitized workflow exports and secret scanning.

## Next

1. **Message-ID deduplication** to make retries safe.
2. **Retries and an error workflow** for HTTP nodes.
3. **Persistent chat memory** in PostgreSQL.
4. **RAG evaluation set** with retrieval and answer quality metrics.
5. **Token expiry alerts** for Instagram credentials.
6. **Observability**: structured logs, failed-message queue, backup alerts.
7. **Named Cloudflare Tunnel** for a stable demo URL.
8. **Scheduled backups**: cron, systemd timer or a CI job with B2 credentials,
   plus a dead-man's-switch alert. Deferred because the current host is local
   and not permanently powered on.

## Later

- Google Calendar reservations.
- Cancellation and modification flows.
- Daily summary.
- Multi-language answers.
- Operator dashboard.
- Per-tenant onboarding CLI.

## Not planned

- A full CRM.
- Invoicing or inventory.
- Kubernetes.
- A multi-provider chatbot platform.
