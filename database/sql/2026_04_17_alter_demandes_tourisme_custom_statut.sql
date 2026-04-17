ALTER TABLE demandes_tourisme_custom
ADD COLUMN IF NOT EXISTS statut VARCHAR(50) NOT NULL DEFAULT 'nouvelle';

UPDATE demandes_tourisme_custom
SET statut = 'nouvelle'
WHERE statut IS NULL OR BTRIM(statut) = '';

ALTER TABLE demandes_tourisme_custom
DROP CONSTRAINT IF EXISTS ck_demandes_tourisme_custom_statut;

ALTER TABLE demandes_tourisme_custom
ADD CONSTRAINT ck_demandes_tourisme_custom_statut
CHECK (statut IN ('nouvelle', 'en_cours_de_traitement', 'traitee', 'annulee'));
