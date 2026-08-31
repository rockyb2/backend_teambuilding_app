ALTER TABLE proformas
ADD COLUMN IF NOT EXISTS client_details JSONB NOT NULL DEFAULT '{}'::jsonb;
