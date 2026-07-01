CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(100) NOT NULL UNIQUE,
    source VARCHAR(50) NOT NULL DEFAULT 'site_web',
    locale VARCHAR(10),
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    visitor_name VARCHAR(255),
    visitor_email VARCHAR(255),
    visitor_phone VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_chat_sessions_status
        CHECK (status IN ('active', 'qualified', 'closed', 'abandoned'))
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_chat_messages_role
        CHECK (role IN ('user', 'assistant', 'system'))
);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id
ON chat_messages(session_id);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session_created
ON chat_messages(session_id, created_at);

CREATE INDEX IF NOT EXISTS ix_chat_sessions_status
ON chat_sessions(status);
