# Roadmap

## Implemented

- Instagram DM webhook.
- Tenant resolution by Instagram account.
- Per-tenant Qdrant retrieval.
- Structured Gemini answers.
- Human handoff state machine.
- Telegram operator commands.
- Local RAG demo without Meta.
- Restic backup and restore runbook.
- CI, tests, sanitized workflow exports and secret scanning.

## Next

1. **Meta signature verification** in the n8n workflow.
2. **Message-ID deduplication** to make retries safe.
3. **Retries and an error workflow** for HTTP nodes.
4. **Persistent chat memory** in PostgreSQL.
5. **RAG evaluation set** with retrieval and answer quality metrics.
6. **Token expiry alerts** for Instagram credentials.
7. **Observability**: structured logs, failed-message queue, backup alerts.

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
