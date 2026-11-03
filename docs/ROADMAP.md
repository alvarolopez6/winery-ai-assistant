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
- Restic backup and restore runbook.
- CI, tests, sanitized workflow exports and secret scanning.

## Next

1. **Message-ID deduplication** to make retries safe.
2. **Retries and an error workflow** for HTTP nodes.
3. **Persistent chat memory** in PostgreSQL.
4. **RAG evaluation set** with retrieval and answer quality metrics.
5. **Token expiry alerts** for Instagram credentials.
6. **Observability**: structured logs, failed-message queue, backup alerts.
7. **Named Cloudflare Tunnel** for a stable demo URL.

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
