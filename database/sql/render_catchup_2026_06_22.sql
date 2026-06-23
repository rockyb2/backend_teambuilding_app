-- Migration de rattrapage Render - 2026-06-22
-- A executer d'abord sur une base de test/restauree depuis Render.
-- Le script est concu pour etre rejouable autant que possible.

BEGIN;

-- ============================================================
-- Utilisateurs / audit
-- ============================================================

ALTER TABLE utilisateur
ADD COLUMN IF NOT EXISTS derniere_connexion TIMESTAMP WITH TIME ZONE NULL;

ALTER TABLE demandes_team_building
ADD COLUMN IF NOT EXISTS statut_modifie_le TIMESTAMP WITH TIME ZONE NULL,
ADD COLUMN IF NOT EXISTS statut_modifie_par_id INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS created_by_id INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL;

ALTER TABLE demandes_tourisme
ADD COLUMN IF NOT EXISTS statut_modifie_le TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS statut_modifie_par_id INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS created_by_id INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL;

ALTER TABLE demandes_tourisme_custom
ADD COLUMN IF NOT EXISTS statut VARCHAR(50) NOT NULL DEFAULT 'nouvelle',
ADD COLUMN IF NOT EXISTS source VARCHAR(30) NOT NULL DEFAULT 'site_web',
ADD COLUMN IF NOT EXISTS statut_modifie_le TIMESTAMP NULL,
ADD COLUMN IF NOT EXISTS statut_modifie_par_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_by_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW();

ALTER TABLE demandes_tourisme_custom
ALTER COLUMN statut SET DEFAULT 'nouvelle',
ALTER COLUMN source SET DEFAULT 'site_web',
ALTER COLUMN updated_at SET DEFAULT NOW();

UPDATE demandes_tourisme
SET statut = CASE
    WHEN statut IS NULL OR BTRIM(statut) = '' THEN 'nouvelle'
    WHEN statut = 'en_cours_de_traitement' THEN 'en_traitement'
    WHEN statut = 'traitee' THEN 'terminee'
    ELSE statut
END
WHERE statut IS NULL
   OR BTRIM(statut) = ''
   OR statut IN ('en_cours_de_traitement', 'traitee');

UPDATE demandes_tourisme_custom
SET statut = CASE
    WHEN statut IS NULL OR BTRIM(statut) = '' THEN 'nouvelle'
    WHEN statut = 'en_cours_de_traitement' THEN 'en_traitement'
    WHEN statut = 'traitee' THEN 'terminee'
    ELSE statut
END
WHERE statut IS NULL
   OR BTRIM(statut) = ''
   OR statut IN ('en_cours_de_traitement', 'traitee');

UPDATE demandes_tourisme_custom
SET source = 'site_web'
WHERE source IS NULL OR BTRIM(source) = '';

UPDATE demandes_tourisme_custom
SET updated_at = NOW()
WHERE updated_at IS NULL;

ALTER TABLE demandes_tourisme_custom
ALTER COLUMN statut SET NOT NULL,
ALTER COLUMN source SET NOT NULL,
ALTER COLUMN updated_at SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_demandes_tourisme_custom_created_by
    ON demandes_tourisme_custom(created_by_id);

CREATE INDEX IF NOT EXISTS idx_demandes_tourisme_custom_updated_by
    ON demandes_tourisme_custom(updated_by_id);

-- ============================================================
-- Contraintes de statuts
-- ============================================================

CREATE TABLE IF NOT EXISTS historique_statut_demandes_tourisme (
    id SERIAL PRIMARY KEY,
    demande_tourisme_id INTEGER REFERENCES demandes_tourisme(id) ON DELETE CASCADE,
    demande_tourisme_custom_id INTEGER REFERENCES demandes_tourisme_custom(id) ON DELETE CASCADE,
    ancien_statut VARCHAR(50),
    nouveau_statut VARCHAR(50) NOT NULL,
    commentaire TEXT,
    modifie_par_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    modifie_le TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_historique_statut_une_seule_demande_tourisme CHECK (
        (demande_tourisme_id IS NOT NULL AND demande_tourisme_custom_id IS NULL)
        OR
        (demande_tourisme_id IS NULL AND demande_tourisme_custom_id IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_historique_statut_demandes_tourisme_demande_tourisme_id
    ON historique_statut_demandes_tourisme(demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_historique_statut_demandes_tourisme_demande_tourisme_custom_id
    ON historique_statut_demandes_tourisme(demande_tourisme_custom_id);

UPDATE historique_statut_demandes_tourisme
SET nouveau_statut = CASE
    WHEN nouveau_statut = 'en_cours_de_traitement' THEN 'en_traitement'
    WHEN nouveau_statut = 'traitee' THEN 'terminee'
    ELSE nouveau_statut
END
WHERE nouveau_statut IN ('en_cours_de_traitement', 'traitee');

UPDATE public.offre
SET statut = CASE statut
    WHEN 'envoye' THEN 'envoyee'
    WHEN 'valide' THEN 'validee'
    WHEN 'refuse' THEN 'refusee'
    WHEN 'expire' THEN 'expiree'
    WHEN 'annule' THEN 'annulee'
    ELSE statut
END
WHERE statut IN ('envoye', 'valide', 'refuse', 'expire', 'annule');

ALTER TABLE public.offre
DROP CONSTRAINT IF EXISTS ck_offre_statut;

ALTER TABLE public.offre
ADD CONSTRAINT ck_offre_statut
CHECK (
    statut IN (
        'brouillon',
        'envoyee',
        'validee',
        'refusee',
        'expiree',
        'annulee'
    )
);

ALTER TABLE demandes_tourisme
DROP CONSTRAINT IF EXISTS ck_demandes_tourisme_statut;

ALTER TABLE demandes_tourisme
ADD CONSTRAINT ck_demandes_tourisme_statut
CHECK (
    statut IN (
        'nouvelle',
        'contactee',
        'en_traitement',
        'devis_envoye',
        'en_attente_reponse_client',
        'relance_envoyee',
        'validee',
        'annulee',
        'refusee',
        'terminee'
    )
);

ALTER TABLE demandes_tourisme_custom
DROP CONSTRAINT IF EXISTS ck_demandes_tourisme_custom_statut;

ALTER TABLE demandes_tourisme_custom
ADD CONSTRAINT ck_demandes_tourisme_custom_statut
CHECK (
    statut IN (
        'nouvelle',
        'contactee',
        'en_traitement',
        'devis_envoye',
        'en_attente_reponse_client',
        'relance_envoyee',
        'validee',
        'annulee',
        'refusee',
        'terminee'
    )
);

ALTER TABLE historique_statut_demandes_tourisme
DROP CONSTRAINT IF EXISTS ck_historique_statut_demande_tourisme_nouveau_statut;

ALTER TABLE historique_statut_demandes_tourisme
ADD CONSTRAINT ck_historique_statut_demande_tourisme_nouveau_statut
CHECK (
    nouveau_statut IN (
        'nouvelle',
        'contactee',
        'en_traitement',
        'devis_envoye',
        'en_attente_reponse_client',
        'relance_envoyee',
        'validee',
        'annulee',
        'refusee',
        'terminee'
    )
);

-- ============================================================
-- Circuits touristiques
-- ============================================================

CREATE TABLE IF NOT EXISTS circuits_touristiques (
    id SERIAL PRIMARY KEY,
    titre VARCHAR(255) NOT NULL,
    lieu VARCHAR(255),
    thematique VARCHAR(255),
    description TEXT,
    details JSONB NOT NULL DEFAULT '[]'::jsonb,
    duree VARCHAR(120),
    prix_base NUMERIC(12, 2) NOT NULL DEFAULT 0,
    categorie VARCHAR(50) NOT NULL DEFAULT 'local',
    type_circuit VARCHAR(100),
    images JSONB NOT NULL DEFAULT '[]'::jsonb,
    itineraire JSONB NOT NULL DEFAULT '[]'::jsonb,
    formules JSONB NOT NULL DEFAULT '[]'::jsonb,
    inclus JSONB NOT NULL DEFAULT '[]'::jsonb,
    non_inclus JSONB NOT NULL DEFAULT '[]'::jsonb,
    conditions_annulation JSONB NOT NULL DEFAULT '[]'::jsonb,
    actif BOOLEAN NOT NULL DEFAULT true,
    publie BOOLEAN NOT NULL DEFAULT false,
    created_by_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    updated_by_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_circuits_touristiques_prix_base_non_negatif CHECK (prix_base >= 0),
    CONSTRAINT ck_circuits_touristiques_categorie CHECK (categorie IN ('local', 'international'))
);

CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_created_by
    ON circuits_touristiques(created_by_id);
CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_actif
    ON circuits_touristiques(actif);
CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_publie
    ON circuits_touristiques(publie);
CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_categorie
    ON circuits_touristiques(categorie);
CREATE INDEX IF NOT EXISTS idx_circuits_touristiques_type
    ON circuits_touristiques(type_circuit);

CREATE TABLE IF NOT EXISTS circuits_touristiques_translations (
    id SERIAL PRIMARY KEY,
    circuit_id INTEGER NOT NULL REFERENCES circuits_touristiques(id) ON DELETE CASCADE,
    langue VARCHAR(10) NOT NULL,
    titre VARCHAR(255) NOT NULL,
    lieu VARCHAR(255),
    thematique VARCHAR(255),
    description TEXT,
    details JSONB NOT NULL DEFAULT '[]'::jsonb,
    duree VARCHAR(120),
    type_circuit VARCHAR(100),
    itineraire JSONB NOT NULL DEFAULT '[]'::jsonb,
    formules JSONB NOT NULL DEFAULT '[]'::jsonb,
    inclus JSONB NOT NULL DEFAULT '[]'::jsonb,
    non_inclus JSONB NOT NULL DEFAULT '[]'::jsonb,
    conditions_annulation JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_circuit_langue UNIQUE (circuit_id, langue),
    CONSTRAINT ck_circuit_translation_langue CHECK (langue IN ('fr', 'en', 'es'))
);

-- ============================================================
-- Newsletter
-- ============================================================

CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    langue VARCHAR(10),
    source VARCHAR(50) NOT NULL DEFAULT 'site_web',
    consentement BOOLEAN NOT NULL DEFAULT true,
    actif BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_email
    ON newsletter_subscribers(email);
CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_actif
    ON newsletter_subscribers(actif);
CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_created_at
    ON newsletter_subscribers(created_at);

-- ============================================================
-- Sites / benevoles / ressources team building
-- ============================================================

ALTER TABLE site
ADD COLUMN IF NOT EXISTS images JSONB NOT NULL DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS a_restauration BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS tarifs_restauration JSONB NULL,
ADD COLUMN IF NOT EXISTS a_salle_seminaire BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN IF NOT EXISTS tarifs_seminaire JSONB NULL,
ADD COLUMN IF NOT EXISTS contact_site VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS email_site VARCHAR(255) NULL;

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
        WHERE table_schema = 'public'
          AND table_name = 'site'
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
          AND conrelid = 'public.site'::regclass
    ) THEN
        ALTER TABLE site
        ADD CONSTRAINT site_images_is_array
        CHECK (jsonb_typeof(images) = 'array');
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'site_tarifs_restauration_is_object'
          AND conrelid = 'public.site'::regclass
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
          AND conrelid = 'public.site'::regclass
    ) THEN
        ALTER TABLE site
        ADD CONSTRAINT site_tarifs_seminaire_is_object
        CHECK (
            tarifs_seminaire IS NULL
            OR jsonb_typeof(tarifs_seminaire) = 'object'
        );
    END IF;
END $$;

UPDATE public.site
SET tarifs_restauration = NULL
WHERE tarifs_restauration = 'null'::jsonb;

UPDATE public.site
SET tarifs_seminaire = NULL
WHERE tarifs_seminaire = 'null'::jsonb;

CREATE INDEX IF NOT EXISTS idx_site_a_restauration
    ON site (a_restauration);
CREATE INDEX IF NOT EXISTS idx_site_a_salle_seminaire
    ON site (a_salle_seminaire);

DROP TABLE IF EXISTS site_images;

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

-- ============================================================
-- Materiel / jeux / activites
-- ============================================================

ALTER TABLE materiel
ADD COLUMN IF NOT EXISTS marque VARCHAR(100) NULL,
ADD COLUMN IF NOT EXISTS modele VARCHAR(150) NULL;

CREATE INDEX IF NOT EXISTS ix_materiel_marque ON materiel (marque);
CREATE INDEX IF NOT EXISTS ix_materiel_modele ON materiel (modele);

CREATE TABLE IF NOT EXISTS jeu_materiel (
    id SERIAL PRIMARY KEY,
    jeu_id INTEGER NOT NULL REFERENCES jeu(id_jeu) ON DELETE CASCADE,
    materiel_id INTEGER NOT NULL REFERENCES materiel(id) ON DELETE CASCADE,
    quantite_requise INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_jeu_materiel UNIQUE (jeu_id, materiel_id),
    CONSTRAINT ck_jeu_materiel_quantite_requise_pos CHECK (quantite_requise > 0)
);

CREATE INDEX IF NOT EXISTS ix_jeu_materiel_jeu_id ON jeu_materiel (jeu_id);
CREATE INDEX IF NOT EXISTS ix_jeu_materiel_materiel_id ON jeu_materiel (materiel_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.activite'::regclass
          AND conname = 'activite_id_offre_key'
    ) THEN
        ALTER TABLE public.activite
        ADD CONSTRAINT activite_id_offre_key UNIQUE (offre_id);
    END IF;
END $$;

DROP INDEX IF EXISTS public.ix_activite_offre_id;

-- ============================================================
-- Offres tourisme
-- ============================================================

CREATE TABLE IF NOT EXISTS offre_tourisme (
    id SERIAL PRIMARY KEY,
    demande_tourisme_id INTEGER REFERENCES demandes_tourisme(id) ON DELETE CASCADE,
    demande_tourisme_custom_id INTEGER REFERENCES demandes_tourisme_custom(id) ON DELETE CASCADE,
    reference VARCHAR(50) NOT NULL UNIQUE,
    titre VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    statut VARCHAR(30) NOT NULL DEFAULT 'brouillon',
    montant_total NUMERIC(12, 2) NOT NULL,
    date_envoi DATE,
    date_validation DATE,
    date_expiration DATE,
    conditions_paiement TEXT,
    observations TEXT,
    created_by_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_offre_tourisme_une_seule_demande CHECK (
        (demande_tourisme_id IS NOT NULL AND demande_tourisme_custom_id IS NULL)
        OR
        (demande_tourisme_id IS NULL AND demande_tourisme_custom_id IS NOT NULL)
    ),
    CONSTRAINT ck_offre_tourisme_statut CHECK (
        statut IN ('brouillon', 'envoyee', 'validee', 'refusee', 'expiree', 'annulee')
    ),
    CONSTRAINT ck_offre_tourisme_montant_total_non_negatif CHECK (montant_total >= 0)
);

CREATE INDEX IF NOT EXISTS ix_offre_tourisme_demande_tourisme_id
    ON offre_tourisme(demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_offre_tourisme_demande_tourisme_custom_id
    ON offre_tourisme(demande_tourisme_custom_id);

-- ============================================================
-- Proformas tourisme
-- ============================================================

ALTER TABLE proformas
ADD COLUMN IF NOT EXISTS pole VARCHAR(30) NOT NULL DEFAULT 'teambuilding',
ADD COLUMN IF NOT EXISTS demande_tourisme_id INTEGER NULL REFERENCES demandes_tourisme(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS demande_tourisme_custom_id INTEGER NULL REFERENCES demandes_tourisme_custom(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS offre_tourisme_id INTEGER NULL REFERENCES offre_tourisme(id) ON DELETE SET NULL;

ALTER TABLE proformas
ALTER COLUMN pole SET DEFAULT 'teambuilding';

UPDATE proformas
SET pole = 'teambuilding'
WHERE pole IS NULL
   OR pole NOT IN ('teambuilding', 'tourisme');

ALTER TABLE proformas
ALTER COLUMN pole SET NOT NULL;

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

COMMIT;
