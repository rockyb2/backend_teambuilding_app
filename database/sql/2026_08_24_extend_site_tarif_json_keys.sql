BEGIN;

-- Les nouveaux champs de la page Sites sont stockés dans les JSONB existants.
-- Aucun ajout de colonne spécifique n'est nécessaire pour :
-- - tarifs_restauration.petit_dejeuner
-- - tarifs_restauration.pause_cafe
-- - tarifs_restauration.dejeuner
-- - tarifs_restauration.gouter
-- - tarifs_restauration.diner
-- - tarifs_restauration.boisson
-- - tarifs_restauration.droit_bouchon
-- - tarifs_seminaire.capacite_salle
-- - tarifs_seminaire.demi_journee
-- - tarifs_seminaire.journee

ALTER TABLE site
  ADD COLUMN IF NOT EXISTS a_restauration boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS tarifs_restauration jsonb NULL,
  ADD COLUMN IF NOT EXISTS a_salle_seminaire boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS tarifs_seminaire jsonb NULL;

UPDATE site
SET tarifs_restauration = NULL
WHERE tarifs_restauration = 'null'::jsonb;

UPDATE site
SET tarifs_seminaire = NULL
WHERE tarifs_seminaire = 'null'::jsonb;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'site_tarifs_restauration_is_object'
      AND conrelid = 'site'::regclass
  ) THEN
    ALTER TABLE site
      ADD CONSTRAINT site_tarifs_restauration_is_object
      CHECK (
        tarifs_restauration IS NULL
        OR jsonb_typeof(tarifs_restauration) = 'object'
      );
  END IF;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'site_tarifs_seminaire_is_object'
      AND conrelid = 'site'::regclass
  ) THEN
    ALTER TABLE site
      ADD CONSTRAINT site_tarifs_seminaire_is_object
      CHECK (
        tarifs_seminaire IS NULL
        OR jsonb_typeof(tarifs_seminaire) = 'object'
      );
  END IF;
END $$;

COMMENT ON COLUMN site.tarifs_restauration IS
  'JSON des tarifs restauration : petit_dejeuner, pause_cafe, dejeuner, gouter, diner, boisson, droit_bouchon.';

COMMENT ON COLUMN site.tarifs_seminaire IS
  'JSON des infos salle séminaire : capacite_salle, demi_journee, journee.';

COMMIT;
