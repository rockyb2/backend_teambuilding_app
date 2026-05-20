CREATE TABLE IF NOT EXISTS site_images (
    id SERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES site(id_site) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    alt VARCHAR(255),
    ordre INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_site_images_site_id
    ON site_images(site_id);

INSERT INTO site_images (site_id, image_url, alt, ordre)
SELECT id_site, image_site, nom_site, 0
FROM site
WHERE image_site IS NOT NULL
  AND BTRIM(image_site) <> ''
  AND NOT EXISTS (
      SELECT 1
      FROM site_images
      WHERE site_images.site_id = site.id_site
        AND site_images.image_url = site.image_site
  );

CREATE TABLE IF NOT EXISTS benevoles (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenoms VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    telephone VARCHAR(30),
    lieu_habitation VARCHAR(255),
    experience TEXT,
    actif BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    id_utilisateur_create INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_benevoles_email
    ON benevoles(email);

CREATE INDEX IF NOT EXISTS idx_benevoles_actif
    ON benevoles(actif);
