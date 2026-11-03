-- Reference schema for the Winery AI Assistant.
-- This file is executed automatically by the official PostgreSQL image on
-- first boot (docker-entrypoint-initdb.d). It is intentionally idempotent.

BEGIN;

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    instagram_id TEXT NOT NULL UNIQUE,
    qdrant_collection TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    telegram_chat_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies (id) ON DELETE CASCADE,
    instagram_user_id TEXT NOT NULL,
    instagram_username TEXT,
    status TEXT NOT NULL DEFAULT 'ai'
        CHECK (status IN ('ai', 'human')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (company_id, instagram_user_id)
);

-- Store only encrypted provider tokens here. The demo does not implement
-- application-level encryption; see docs/SECURITY.md before production use.
CREATE TABLE IF NOT EXISTS credentials (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies (id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    encrypted_value TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (company_id, type)
);

CREATE INDEX IF NOT EXISTS idx_conversations_company_status
    ON conversations (company_id, status);

CREATE INDEX IF NOT EXISTS idx_credentials_company_type
    ON credentials (company_id, type);

COMMIT;
