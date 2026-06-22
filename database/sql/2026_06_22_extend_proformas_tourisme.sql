ALTER TABLE proformas
ADD COLUMN IF NOT EXISTS pole VARCHAR(30) NOT NULL DEFAULT 'teambuilding';

ALTER TABLE proformas
ADD COLUMN IF NOT EXISTS demande_tourisme_id INTEGER NULL REFERENCES demandes_tourisme(id) ON DELETE SET NULL;

ALTER TABLE proformas
ADD COLUMN IF NOT EXISTS demande_tourisme_custom_id INTEGER NULL REFERENCES demandes_tourisme_custom(id) ON DELETE SET NULL;

ALTER TABLE proformas
ADD COLUMN IF NOT EXISTS offre_tourisme_id INTEGER NULL REFERENCES offre_tourisme(id) ON DELETE SET NULL;

UPDATE proformas
SET pole = 'teambuilding'
WHERE pole IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.proformas'::regclass
          AND conname = 'ck_proformas_pole'
    ) THEN
        ALTER TABLE proformas
        ADD CONSTRAINT ck_proformas_pole
        CHECK (pole IN ('teambuilding', 'tourisme'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_proformas_pole ON proformas (pole);
CREATE INDEX IF NOT EXISTS ix_proformas_demande_tourisme_id ON proformas (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_proformas_demande_tourisme_custom_id ON proformas (demande_tourisme_custom_id);
CREATE INDEX IF NOT EXISTS ix_proformas_offre_tourisme_id ON proformas (offre_tourisme_id);
