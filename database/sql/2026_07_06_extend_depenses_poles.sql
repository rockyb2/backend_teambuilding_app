ALTER TABLE depense
ADD COLUMN IF NOT EXISTS pole VARCHAR(30) NOT NULL DEFAULT 'teambuilding';

ALTER TABLE depense
ALTER COLUMN activite_id DROP NOT NULL;

ALTER TABLE depense
ADD COLUMN IF NOT EXISTS proforma_id INTEGER NULL REFERENCES proformas(id) ON DELETE SET NULL;

ALTER TABLE depense
ADD COLUMN IF NOT EXISTS facture_id INTEGER NULL REFERENCES facture(id) ON DELETE SET NULL;

ALTER TABLE depense
ADD COLUMN IF NOT EXISTS demande_team_building_id INTEGER NULL REFERENCES demandes_team_building(id) ON DELETE SET NULL;

ALTER TABLE depense
ADD COLUMN IF NOT EXISTS demande_tourisme_id INTEGER NULL REFERENCES demandes_tourisme(id) ON DELETE SET NULL;

ALTER TABLE depense
ADD COLUMN IF NOT EXISTS demande_tourisme_custom_id INTEGER NULL REFERENCES demandes_tourisme_custom(id) ON DELETE SET NULL;

UPDATE depense
SET pole = 'teambuilding'
WHERE pole IS NULL;

UPDATE depense d
SET demande_team_building_id = a.demande_id
FROM activite a
WHERE d.activite_id = a.id
  AND d.demande_team_building_id IS NULL;

UPDATE depense d
SET demande_team_building_id = o.demande_id
FROM offre o
WHERE d.offre_id = o.id
  AND d.demande_team_building_id IS NULL;

ALTER TABLE depense
DROP CONSTRAINT IF EXISTS ck_depense_pole;

ALTER TABLE depense
ADD CONSTRAINT ck_depense_pole
CHECK (pole IN ('teambuilding', 'tourisme', 'production'));

ALTER TABLE depense
DROP CONSTRAINT IF EXISTS depense_activite_id_fkey;

ALTER TABLE depense
ADD CONSTRAINT depense_activite_id_fkey
FOREIGN KEY (activite_id) REFERENCES activite(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_depense_pole ON depense (pole);
CREATE INDEX IF NOT EXISTS ix_depense_proforma_id ON depense (proforma_id);
CREATE INDEX IF NOT EXISTS ix_depense_facture_id ON depense (facture_id);
CREATE INDEX IF NOT EXISTS ix_depense_demande_team_building_id ON depense (demande_team_building_id);
CREATE INDEX IF NOT EXISTS ix_depense_demande_tourisme_id ON depense (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_depense_demande_tourisme_custom_id ON depense (demande_tourisme_custom_id);
