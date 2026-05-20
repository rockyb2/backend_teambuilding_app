CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    langue VARCHAR(10),
    source VARCHAR(50) NOT NULL DEFAULT 'site_web',
    consentement BOOLEAN NOT NULL DEFAULT true,
    actif BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_email
    ON newsletter_subscribers(email);

CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_actif
    ON newsletter_subscribers(actif);

CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_created_at
    ON newsletter_subscribers(created_at);
