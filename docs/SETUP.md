# Setup

This guide covers the full deployment. For the local RAG demo, see the
[README](../README.md#quickstart).

## 1. Prerequisites

- Docker Engine with Compose v2.
- Python 3.11+ for the local demo scripts.
- A Gemini API key.
- Optional: a Meta developer app with an Instagram business account.
- Optional: a Telegram bot.

## 2. Environment

```bash
cp .env.example .env
```

Edit `.env`:

- `POSTGRES_PASSWORD`: use a strong password.
- `N8N_ENCRYPTION_KEY`: generate with `openssl rand -hex 32`.
- `GEMINI_API_KEY`: required for the local demo.
- `N8N_HOST`, `N8N_PROTOCOL`, `N8N_WEBHOOK_URL`: set these to your public host
  when you deploy behind HTTPS.
- `N8N_SECURE_COOKIE=true` when using HTTPS.
- `INSTAGRAM_APP_SECRET` and `INSTAGRAM_VERIFY_TOKEN`: required for the Meta
  webhook.

Never commit `.env`.

## 3. Start the stack

```bash
docker compose up -d
docker compose ps
```

PostgreSQL runs the files in `sql/init/` on first boot. If you change the
schema, add a new migration instead of editing the existing one after a
deployment.

n8n is available at <http://localhost:5678>. Create the owner account on first
access.

## 4. Import the workflows

1. In n8n, go to **Workflows → Import from File**.
2. Import `workflows/main.json` and `workflows/telegram-admin.json`.
3. Create the credentials requested by the nodes:
   - PostgreSQL: host `postgres`, port `5432`, database and user from `.env`.
   - Qdrant: URL `http://qdrant:6333`.
   - Google Gemini: API key.
   - Telegram: bot token.
4. Re-select the credentials in each node. The exports intentionally do not
   include credential IDs.
5. Do not activate the workflows until the webhook and credentials are
   configured.

## 5. Seed a tenant

The demo seed inserts a fictional tenant:

```sql
SELECT id, name, instagram_id, qdrant_collection
FROM companies;
```

For a real tenant, insert a row with its Instagram account ID, Qdrant
collection name and Telegram chat ID.

Add the Instagram token to `credentials.encrypted_value`. The workflow sends
that value as the Bearer token, so if you encrypt it you must decrypt it before
the HTTP node. The demo does not implement application-level encryption; use a
secret manager or a small encryption helper in production. Do not store
plaintext tokens in a shared database. See [`SECURITY.md`](SECURITY.md).

## 6. Build the knowledge base

For the local demo:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/rag_ingest.py --source examples/demo --collection demo_wines --recreate
```

The script infers the vector size from the embedding model. `gemini-embedding-001`
typically returns 3072 dimensions.

For a real tenant, replace `--source` with the tenant's document directory and
`--collection` with the value stored in `companies.qdrant_collection`.

## 7. Configure Meta

1. Create a Meta app with the Instagram Graph API product.
2. Connect the Instagram business account.
3. Add the webhook callback:
   `https://<your-host>/webhook/instagram`.
4. Set the verify token to `INSTAGRAM_VERIFY_TOKEN`.
5. Subscribe to the `messages` field.
6. Copy the app secret into `INSTAGRAM_APP_SECRET`.
7. Add signature verification before exposing the endpoint. See
   [`SECURITY.md`](SECURITY.md).

## 8. Configure Telegram

1. Create a bot with BotFather.
2. Put the bot token in the n8n Telegram credential.
3. Send a message to the bot and read the chat ID from the Telegram trigger
   output.
4. Store that chat ID in `companies.telegram_chat_id`.
5. Activate `telegram-admin.json`.

## 9. Test

- Send a DM to the Instagram account.
- Confirm the reply in Instagram.
- Confirm the `conversations` row changes state when the model escalates.
- Send `/stats` to the Telegram bot.
- Send `/human @username` and verify that the bot stops replying.
- Send `/ai @username` and verify that the bot resumes.

## Troubleshooting

| Symptom | Check |
|---|---|
| n8n cannot reach PostgreSQL | Credential host must be `postgres`, not `localhost` |
| Qdrant collection not found | Run the ingestion script and check `companies.qdrant_collection` |
| Webhook returns 404 | The workflow must be active and the path must be `instagram` |
| Instagram token rejected | Token expired or the app lacks the required permission |
| Telegram alert not sent | `telegram_chat_id` is wrong or the bot was not started |
