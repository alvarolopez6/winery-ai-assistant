# Contributing

## Setup

```bash
cp .env.example .env
# Edit .env: POSTGRES_PASSWORD, N8N_ENCRYPTION_KEY, GEMINI_API_KEY
docker compose up -d
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## Before opening a pull request

```bash
ruff check scripts tests
pytest -q
jq empty workflows/*.json
docker compose config -q
python scripts/sanitize_workflow.py --check workflows/main.json workflows/telegram-admin.json
```

## Style

- Python: Ruff defaults, type hints on public functions, small modules.
- Shell: `set -euo pipefail`, quote variables, ShellCheck clean.
- SQL: idempotent migrations, explicit foreign keys and constraints.
- n8n exports: sanitize before committing; never include credential IDs,
  webhook IDs, execution data or tokens.
- Documentation: describe what exists, not what is planned.

## Secrets

Never commit `.env`, provider tokens, customer data or execution exports. If a
secret reaches a commit, revoke it first, then follow [`SECURITY.md`](SECURITY.md).

## Commit messages

Use short, imperative messages. Examples:

- `Add signature verification step`
- `Fix tenant filter in stats query`
- `Document backup restore procedure`
