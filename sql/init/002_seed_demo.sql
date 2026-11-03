-- Fictional demo tenant. All names, prices and schedules are invented.
-- Do not use this seed as real business data.

INSERT INTO companies (name, instagram_id, qdrant_collection, telegram_chat_id)
VALUES (
    'Bodega Sierra Azul (demo)',
    'demo-instagram-account',
    'demo_wines',
    '0'
)
ON CONFLICT (instagram_id) DO NOTHING;

-- No provider token is seeded on purpose. To exercise the Instagram workflow,
-- add a row to credentials with an encrypted token:
--
--   INSERT INTO credentials (company_id, type, encrypted_value)
--   SELECT id, 'instagram', '<encrypted-token>'
--   FROM companies
--   WHERE instagram_id = 'demo-instagram-account';
--
-- For the local RAG demo, use scripts/rag_ingest.py and scripts/rag_query.py
-- instead. They do not need Instagram credentials.
