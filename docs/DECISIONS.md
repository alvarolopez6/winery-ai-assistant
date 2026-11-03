# Design decisions

## ADR-001: n8n instead of a custom backend

**Context:** the target is a small business that needs an integration quickly.

**Decision:** use n8n for orchestration.

**Consequences:** fast connector work and a visual audit trail, but business
logic lives in JSON. The repository compensates with a small Python demo path,
SQL schema, sanitized exports and tests.

## ADR-002: PostgreSQL for application state

**Context:** n8n already stores its own state in SQLite.

**Decision:** use PostgreSQL for tenants and conversation state.

**Consequences:** a real unique constraint and transactional state, at the cost
of one more service to operate.

## ADR-003: one Qdrant collection per tenant

**Context:** a shared collection with a `company_id` filter is possible.

**Decision:** use one collection per tenant.

**Consequences:** stronger isolation and simple deletion. More collections to
manage at scale.

## ADR-004: explicit human handoff state

**Context:** a model can decide to escalate, but the decision must survive
restarts and operator actions.

**Decision:** persist `ai` / `human` in PostgreSQL and let the operator change
it from Telegram.

**Consequences:** deterministic behavior, but an extra state machine to test.

## ADR-005: Telegram as the operator channel

**Context:** the business owner needs a lightweight interface.

**Decision:** use a Telegram bot with four commands.

**Consequences:** low friction, but Telegram becomes part of the personal-data
surface. Document it in the privacy notice.

## ADR-006: local Python RAG demo

**Context:** a reviewer should be able to test retrieval without a Meta app.

**Decision:** ship `scripts/rag_ingest.py` and `scripts/rag_query.py` using the
same embedding model and collection shape as n8n.

**Consequences:** the demo needs a Gemini key, but not Instagram. The scripts
also provide a small, testable code path.

## ADR-007: no reservation flow yet

**Context:** the original roadmap included Google Calendar reservations.

**Decision:** do not claim or ship an unimplemented reservation flow.

**Consequences:** the README and roadmap are honest. Reservations are a future
integration, not a hidden feature.

## ADR-008: public gateway outside n8n

**Context:** Meta needs a GET challenge and HMAC signature verification. Doing
both inside n8n would require exposing environment variables to nodes or
storing the verify token in workflow JSON, and n8n would have to be the public
service.

**Decision:** put a small FastAPI gateway in front of n8n. The gateway handles
Meta GET verification and `X-Hub-Signature-256`, proxies Telegram webhook paths
with their secret header, then forwards valid POSTs over the private Docker
network.

**Consequences:** n8n stays private, signature verification is testable in
Python, and Cloudflare or a reverse proxy only needs to expose one small
service. The cost is one more container and one more deployment artifact.
