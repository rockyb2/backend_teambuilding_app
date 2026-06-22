BEGIN;

ALTER TABLE site
  ADD COLUMN IF NOT EXISTS images jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS a_restauration boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS tarifs_restauration jsonb NULL,
  ADD COLUMN IF NOT EXISTS a_salle_seminaire boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS tarifs_seminaire jsonb NULL;

DO $$
BEGIN
  IF to_regclass('public.site_images') IS NOT NULL THEN
    UPDATE site AS s
    SET images = migrated.images
    FROM (
      SELECT
        site_id,
        jsonb_agg(image_url ORDER BY ordre, id) AS images
      FROM site_images
      WHERE image_url IS NOT NULL
        AND btrim(image_url) <> ''
      GROUP BY site_id
    ) AS migrated
    WHERE s.id_site = migrated.site_id
      AND jsonb_array_length(COALESCE(s.images, '[]'::jsonb)) = 0;
  END IF;

  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'site'
      AND column_name = 'image_site'
  ) THEN
    UPDATE site
    SET images = jsonb_build_array(image_site)
    WHERE image_site IS NOT NULL
      AND btrim(image_site) <> ''
      AND jsonb_array_length(COALESCE(images, '[]'::jsonb)) = 0;

    ALTER TABLE site DROP COLUMN image_site;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'site_images_is_array'
      AND conrelid = 'site'::regclass
  ) THEN
    ALTER TABLE site
      ADD CONSTRAINT site_images_is_array
      CHECK (jsonb_typeof(images) = 'array');
  END IF;

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

CREATE INDEX IF NOT EXISTS idx_site_a_restauration
  ON site (a_restauration);

CREATE INDEX IF NOT EXISTS idx_site_a_salle_seminaire
  ON site (a_salle_seminaire);

DROP TABLE IF EXISTS site_images;

COMMIT;
