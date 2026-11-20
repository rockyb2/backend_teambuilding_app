ALTER TABLE budgets ADD COLUMN IF NOT EXISTS pole VARCHAR(30) NOT NULL DEFAULT 'teambuilding';
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS offre_tourisme_id INTEGER NULL REFERENCES offre_tourisme(id) ON DELETE CASCADE;
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS demande_tourisme_id INTEGER NULL REFERENCES demandes_tourisme(id) ON DELETE SET NULL;
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS demande_tourisme_custom_id INTEGER NULL REFERENCES demandes_tourisme_custom(id) ON DELETE SET NULL;
ALTER TABLE budgets ALTER COLUMN offre_id DROP NOT NULL;

CREATE INDEX IF NOT EXISTS ix_budgets_pole ON budgets(pole);
CREATE INDEX IF NOT EXISTS ix_budgets_offre_tourisme_id ON budgets(offre_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_budgets_demande_tourisme_id ON budgets(demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_budgets_demande_tourisme_custom_id ON budgets(demande_tourisme_custom_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_budgets_offre_tourisme_valide
ON budgets(offre_tourisme_id)
WHERE statut = 'valide' AND offre_tourisme_id IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_budgets_pole') THEN
        ALTER TABLE budgets ADD CONSTRAINT ck_budgets_pole CHECK (pole IN ('teambuilding', 'tourisme'));
    END IF;
END $$;
