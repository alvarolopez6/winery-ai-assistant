# Security

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use GitHub Security
Advisories on the repository, or contact the maintainer privately.

## Secrets

- `.env` is ignored by Git. Only `.env.example` is committed.
- `N8N_ENCRYPTION_KEY` protects n8n credentials at rest. Back it up separately
  from the n8n database; without it, the credentials cannot be decrypted.
- Provider tokens belong in the `credentials` table or in n8n credentials, not
  in workflow JSON.
- Rotate any token that was ever stored in plaintext, shared in a chat, or
  committed by mistake.
- Do not paste secrets into issues, pull requests or screenshots.

## Webhook security

The exported n8n workflow validates the event shape but **does not verify
Meta's `X-Hub-Signature-256` header**. This is a known limitation. Do not expose
the webhook to the public internet until you add verification.

Required production controls:

1. Capture the raw request body before JSON parsing.
2. Compute `HMAC-SHA256(app_secret, raw_body)`.
3. Compare it with `X-Hub-Signature-256` using a constant-time comparison.
4. Reject requests with a missing or invalid signature.
5. Verify `body.object == "instagram"`.
6. Ignore `message.is_echo` events and non-text events.
7. Deduplicate by message ID to avoid duplicate replies on Meta retries.
8. Rate-limit the endpoint at the reverse proxy or WAF.

Additional hardening:

- Put n8n behind a reverse proxy with TLS.
- Require authentication for the n8n editor.
- Do not expose PostgreSQL or Qdrant to the host or the internet.
- If Qdrant must be reachable, set `QDRANT_API_KEY` and bind it to a private
  network.

## Tenant isolation

- Every query that touches conversations must filter by `company_id`.
- Every Qdrant retrieval must use the tenant's collection.
- The `(company_id, instagram_user_id)` unique constraint is part of the
  security model, not just a data-model detail.
- Add a regression test before adding a new endpoint that queries tenant data.

## Personal data

The system stores Instagram user IDs, usernames and conversation state. If you
operate it with real customers:

- Establish a lawful basis and publish a privacy notice.
- Define a retention period for conversations and execution data.
- Provide a way to delete a customer's data.
- Sign data-processing agreements with Meta, Google and Telegram where
  required.
- Avoid sending more personal data to the LLM than necessary.
- Remember that Telegram alerts include the customer's username and the reason
  for escalation.

## Execution data

n8n can store node inputs and outputs, including the `Authorization` header used
to call Meta. The Compose file mitigates this with:

- `EXECUTIONS_DATA_PRUNE=true`
- `EXECUTIONS_DATA_MAX_AGE=168`
- `EXECUTIONS_DATA_SAVE_ON_SUCCESS=none`

Review the n8n execution settings before production. If you need full execution
history for debugging, restrict access to the database and encrypt backups.

## Backups

- Restic encrypts the repository; the Restic password is mandatory.
- The staging directory contains a plaintext PostgreSQL dump and a copy of the
  n8n state. Restrict its permissions and delete old staging files.
- Back up the n8n encryption key separately. A backup of the database without
  the key cannot restore credentials.
- Test a restore before trusting the backup.

## Production checklist

- [ ] Rotate every credential that was ever stored in plaintext.
- [ ] Set a strong `POSTGRES_PASSWORD`.
- [ ] Set `N8N_ENCRYPTION_KEY` and store it outside the repository.
- [ ] Set `N8N_SECURE_COOKIE=true` and serve n8n over HTTPS.
- [ ] Put n8n behind authentication.
- [ ] Add Meta signature verification.
- [ ] Add rate limiting.
- [ ] Add message-ID deduplication.
- [ ] Set `QDRANT_API_KEY` if Qdrant is reachable outside the Docker network.
- [ ] Restrict PostgreSQL to the Docker network.
- [ ] Configure backup retention and test a restore.
- [ ] Publish a privacy notice and retention policy.
- [ ] Review provider terms (Meta, Google, Telegram, n8n).
