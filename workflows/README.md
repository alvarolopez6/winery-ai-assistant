# n8n workflows

These are sanitized exports of the n8n workflows. They contain no credential
IDs, webhook IDs or execution data.

## Files

| File | Purpose |
|---|---|
| `main.json` | Instagram webhook, tenant resolution, RAG, handoff |
| `telegram-admin.json` | Operator commands over Telegram |

## Import

1. Open n8n.
2. **Workflows → Import from File**.
3. Import both JSON files.
4. Create and select the required credentials:
   - PostgreSQL
   - Qdrant
   - DeepSeek (chat model)
   - Google Gemini (embeddings)
   - Telegram
5. Activate the workflows only after the credentials and webhook are ready.

## Webhook

`main.json` expects:

```text
POST /webhook/instagram
```

The exported workflow filters non-Instagram payloads, echoes and non-text
events. It does **not** verify `X-Hub-Signature-256`; see
[`../docs/SECURITY.md`](../docs/SECURITY.md) before exposing it.

## Regenerating an export

Export from n8n, then run:

```bash
python scripts/sanitize_workflow.py raw-export.json workflows/main.json
```

The sanitizer removes instance metadata and refuses to write a file that looks
like it contains a token.
