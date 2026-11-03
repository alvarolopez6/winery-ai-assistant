SHELL := /bin/bash
PYTHON ?= python3
.DEFAULT_GOAL := help

.PHONY: help env up down logs ps restart ingest ask test lint validate tunnel backup clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

env: ## Create .env from .env.example if it does not exist
	@test -f .env || (cp .env.example .env && echo "Created .env — edit it before starting the stack.")

up: env ## Start PostgreSQL, Qdrant and n8n
	docker compose up -d

down: ## Stop the stack
	docker compose down

logs: ## Follow service logs
	docker compose logs -f --tail=100

ps: ## Show service status
	docker compose ps

restart: ## Restart the stack
	docker compose restart

ingest: ## Rebuild the demo Qdrant collection
	$(PYTHON) scripts/rag_ingest.py --recreate

ask: ## Ask the demo assistant: make ask Q="..."
	@test -n "$(Q)" || (echo 'Usage: make ask Q="¿Qué vino recomiendas?"' && exit 1)
	$(PYTHON) scripts/rag_query.py "$(Q)"

test: ## Run the test suite
	pytest -q

lint: ## Run Ruff
	ruff check scripts tests

validate: ## Validate workflows and compose file
	$(PYTHON) scripts/sanitize_workflow.py --check workflows/main.json workflows/telegram-admin.json
	docker compose config -q

tunnel: ## Start a Cloudflare quick tunnel for the gateway
	cloudflared tunnel --url http://localhost:8080

backup: ## Run the Restic backup
	./scripts/backup.sh

clean: ## Stop the stack and delete its volumes (destructive)
	docker compose down -v
