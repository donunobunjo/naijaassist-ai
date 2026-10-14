-- NaijaMobile AI demo schema. Requires PostgreSQL and pgvector.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku TEXT NOT NULL UNIQUE,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('Phone', 'Tablet', 'Accessory')),
    condition TEXT NOT NULL CHECK (condition IN ('New', 'Refurbished', 'Used')),
    description TEXT NOT NULL,
    ram_gb INTEGER CHECK (ram_gb IS NULL OR ram_gb >= 0),
    storage_gb INTEGER CHECK (storage_gb IS NULL OR storage_gb >= 0),
    display_inches NUMERIC(5,2),
    battery_mah INTEGER CHECK (battery_mah IS NULL OR battery_mah >= 0),
    camera_mp NUMERIC(6,2),
    os TEXT,
    connectivity TEXT,
    warranty_months INTEGER CHECK (warranty_months IS NULL OR warranty_months >= 0),
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_prices (
    sku TEXT PRIMARY KEY REFERENCES products(sku) ON DELETE CASCADE,
    price_ngn NUMERIC(14,2) NOT NULL CHECK (price_ngn >= 0),
    updated_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('approved', 'pending', 'retired')),
    approved_by TEXT,
    approved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS product_price_history (
    id BIGSERIAL PRIMARY KEY,
    sku TEXT NOT NULL REFERENCES products(sku) ON DELETE CASCADE,
    old_price_ngn NUMERIC(14,2),
    new_price_ngn NUMERIC(14,2) NOT NULL CHECK (new_price_ngn >= 0),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    changed_by TEXT NOT NULL,
    change_source TEXT NOT NULL DEFAULT 'admin',
    reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_price_history_sku_changed ON product_price_history(sku, changed_at DESC);

CREATE TABLE IF NOT EXISTS inventory (
    sku TEXT PRIMARY KEY REFERENCES products(sku) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    whatsapp_id TEXT UNIQUE,
    phone_e164 TEXT UNIQUE,
    display_name TEXT,
    consent_status TEXT NOT NULL DEFAULT 'unknown' CHECK (consent_status IN ('unknown','granted','withdrawn')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    channel TEXT NOT NULL DEFAULT 'whatsapp',
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','pending_human','resolved','closed')),
    assigned_to TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_conversations_customer_recent ON conversations(customer_id, last_message_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    provider_message_id TEXT UNIQUE,
    direction TEXT NOT NULL CHECK (direction IN ('inbound','outbound')),
    message_type TEXT NOT NULL DEFAULT 'text',
    body TEXT,
    delivery_status TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_time ON messages(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS customer_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    source_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    consent_basis TEXT NOT NULL DEFAULT 'conversation_context',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ,
    UNIQUE(customer_id, memory_key)
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_path TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    version TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);

CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    conversation_id UUID REFERENCES conversations(id),
    category TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','assigned','waiting_customer','resolved','closed')),
    summary TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal' CHECK (priority IN ('low','normal','high','urgent')),
    assigned_to TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS webhook_events (
    id BIGSERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    provider_event_id TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'received' CHECK (status IN ('received','processing','processed','failed','ignored')),
    error_summary TEXT,
    UNIQUE(provider, provider_event_id)
);

CREATE TABLE IF NOT EXISTS price_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    sku TEXT NOT NULL REFERENCES products(sku) ON DELETE CASCADE,
    target_price_ngn NUMERIC(14,2) NOT NULL CHECK (target_price_ngn >= 0),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','triggered','cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    triggered_at TIMESTAMPTZ
);

-- Prices must only be quoted by application code when status='approved' and freshness is valid.
-- Do not store authoritative prices in vector embeddings.
