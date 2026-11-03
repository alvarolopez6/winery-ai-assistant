# Setup

This guide covers the full deployment. For the local RAG demo, see the
[README](../README.md#quickstart).

## 1. Prerequisites

- Docker Engine with Compose v2.
- Python 3.11+ for the local demo scripts.
- A Gemini API key.
- Optional: a Meta developer app with an Instagram business account.
- Optional: a Telegram bot.
- Optional: Cloudflare Tunnel for a public demo URL.

## 2. Environment

```bash
cp .env.example .env
```

Edit `.env`:

- `POSTGRES_PASSWORD`: use a strong password.
- `N8N_ENCRYPTION_KEY`: generate with `openssl rand -hex 32`.
- `GEMINI_API_KEY`: required for the local demo.
- `N8N_HOST`, `N8N_PROTOCOL`: set these for the n8n editor when you deploy
  behind HTTPS.
- `PUBLIC_BASE_URL`: public URL of the gateway. Locally it is
  `http://localhost:8080/`; with Cloudflare it is the tunnel URL.
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

n8n is available at <http://localhost:5678>. The gateway is available at
<http://localhost:8080> and is the only public entry point. Create the n8n owner
account on first access.

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

## 7. Expose the gateway

For a quick demo, start a Cloudflare quick tunnel against the gateway:

```bash
cloudflared tunnel --url http://localhost:8080
```

Copy the generated `https://...trycloudflare.com` URL into `PUBLIC_BASE_URL` in
`.env` and restart n8n so its webhook display uses the public base:

```bash
docker compose up -d n8n
```

Quick tunnels are for demos only. For production, use a named Cloudflare Tunnel
or a reverse proxy with a stable domain. Never point the tunnel at n8n itself.

The Telegram Trigger uses the same public gateway URL. n8n registers a
`/webhook/<uuid>/webhook` path; the gateway proxies it to n8n and forwards the
Telegram secret header. Do not expose n8n directly.

## 8. Configure Meta

1. Create a Meta app with the Instagram Graph API product.
2. Connect the Instagram business account.
3. Add the webhook callback:
   `https://<your-host>/webhook/instagram`.
4. Set the verify token to the same value as `INSTAGRAM_VERIFY_TOKEN`.
5. Subscribe to the `messages` field.
6. Copy the app secret into `INSTAGRAM_APP_SECRET`.
7. Keep the gateway as the only public endpoint. It validates the token and the
   `X-Hub-Signature-256` header before forwarding to n8n. See
   [`SECURITY.md`](SECURITY.md).

## 9. Configure Telegram

1. Create a bot with BotFather.
2. Put the bot token in the n8n Telegram credential.
3. Send a message to the bot and read the chat ID from the Telegram trigger
   output.
4. Store that chat ID in `companies.telegram_chat_id`.
5. Activate `telegram-admin.json`.

## 10. Test

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
| Webhook returns 404 | The n8n workflow must be active and the path must be `instagram` |
| Meta verification fails | Gateway not running, or `PUBLIC_BASE_URL` does not match the tunnel |
| Instagram token rejected | Token expired or the app lacks the required permission |
| Telegram alert not sent | `telegram_chat_id` is wrong or the bot was not started |
