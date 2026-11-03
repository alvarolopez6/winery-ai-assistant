# Workflows

## Main workflow

`workflows/main.json` handles one Instagram DM at a time after the gateway has
verified the request.

| Node | Responsibility |
|---|---|
| `Webhook` | Receives `POST /webhook/instagram` |
| `Filter Event` | Ignores non-Instagram payloads, echoes and non-text messages |
| `QueryID` | Resolves the tenant by Instagram recipient ID |
| `QueryEncrypted` | Loads the tenant's Instagram token |
| `HTTPInstagramInfo` | Fetches the customer's `name` and `username` |
| `FirstConversationInsert` | Creates the conversation row if missing |
| `AiHumanQuery` | Reads `ai` / `human` state |
| `If1` | Branches between bot and human mode |
| `AI Agent` | Retrieves context and generates a structured answer |
| `Google Gemini Chat Model` | Answer model |
| `Qdrant Vector Store` | Tenant-scoped retrieval tool |
| `Embeddings Google Gemini` | Embeddings for retrieval |
| `Simple Memory` | Per-conversation short-term memory |
| `Structured Output Parser` | Enforces `reply`, `needs_human`, `reason` |
| `If` | Branches on `needs_human` |
| `HTTPRespuesta` | Sends the AI reply to Instagram |
| `SetConversationHuman` | Persists the handoff state |
| `HTTPMensajeEspera` | Sends the handoff message |
| `TelegramIA` | Notifies the operator |

### Event guard

The `Filter Event` code node rejects:

- Payloads whose `object` is not `instagram`.
- Events without `message.text`.
- Echo events (`message.is_echo`).

This prevents the bot from replying to its own messages and from crashing on
reactions or attachments.

## Telegram admin workflow

`workflows/telegram-admin.json` is restricted to the chat ID stored in
`companies.telegram_chat_id`.

| Command | Effect |
|---|---|
| `/ai @username` | Returns a conversation to the bot |
| `/human @username` | Moves a conversation to human mode |
| `/stats` | Shows counts for the operator's company |
| `/help` | Shows the command list |

The `IfAllowed` node drops messages from chat IDs that do not match a company.

## Known limitations

- Meta signature verification is handled by the gateway, not by these
  workflows. Never expose n8n directly.
- Only the first entry and the first message of a webhook are processed.
- Meta retries can produce duplicate replies; add message-ID deduplication.
- HTTP nodes have no retry policy.
- Chat memory is in RAM and is lost on restart.
- The n8n ingestion workflow is not implemented; use
  `scripts/rag_ingest.py` for the demo.

## Editing safely

1. Export the workflow from n8n.
2. Sanitize it:

   ```bash
   python scripts/sanitize_workflow.py raw.json workflows/main.json
   ```

3. Run `pytest -q` and `jq empty workflows/main.json`.
4. Import the result into a clean n8n instance and smoke-test it.
