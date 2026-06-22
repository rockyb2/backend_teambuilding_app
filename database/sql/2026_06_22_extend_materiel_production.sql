ALTER TABLE materiel
ADD COLUMN IF NOT EXISTS marque VARCHAR(100) NULL;

ALTER TABLE materiel
ADD COLUMN IF NOT EXISTS modele VARCHAR(150) NULL;

CREATE INDEX IF NOT EXISTS ix_materiel_marque ON materiel (marque);
CREATE INDEX IF NOT EXISTS ix_materiel_modele ON materiel (modele);
