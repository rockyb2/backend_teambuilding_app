ALTER TABLE demandes_tourisme_custom
ADD COLUMN IF NOT EXISTS source VARCHAR(30) NOT NULL DEFAULT 'site_web',
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_demandes_tourisme_custom_created_by
    ON demandes_tourisme_custom(created_by_id);

CREATE INDEX IF NOT EXISTS idx_demandes_tourisme_custom_updated_by
    ON demandes_tourisme_custom(updated_by_id);
