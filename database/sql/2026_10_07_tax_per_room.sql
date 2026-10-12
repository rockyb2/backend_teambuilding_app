ALTER TABLE proformas ADD COLUMN IF NOT EXISTS nombre_chambres INTEGER NOT NULL DEFAULT 0;
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS nombre_chambres INTEGER NOT NULL DEFAULT 0;

ALTER TABLE taxes DROP CONSTRAINT IF EXISTS taxes_type_calcul_check;
UPDATE taxes
SET type_calcul = 'forfait_chambre_nuit',
    description = CASE WHEN code = 'NUITEE' THEN 'Calculée par chambre et par nuitée' ELSE description END
WHERE type_calcul = 'forfait_personne_nuit' OR code = 'NUITEE';
ALTER TABLE taxes
ADD CONSTRAINT taxes_type_calcul_check
CHECK (type_calcul IN ('pourcentage', 'pourcentage_lignes', 'forfait_chambre_nuit'));
