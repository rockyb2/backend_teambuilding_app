-- Extension de la base transport: véhicules, trajets, péages et tarifs détaillés.
-- Script idempotent pour PostgreSQL.

CREATE TABLE IF NOT EXISTS public.vehicules_transport (
    id SERIAL PRIMARY KEY,
    fournisseur_id INTEGER NOT NULL REFERENCES public.fournisseurs_transport(id) ON DELETE CASCADE,
    type_vehicule VARCHAR(50) NOT NULL,
    libelle VARCHAR(255) NOT NULL,
    nombre_places INTEGER NULL,
    climatisation BOOLEAN NOT NULL DEFAULT false,
    chauffeur_inclus BOOLEAN NOT NULL DEFAULT true,
    carburant_inclus BOOLEAN NOT NULL DEFAULT false,
    classe_peage VARCHAR(50) NULL,
    immatriculation VARCHAR(80) NULL,
    assurance_expiration DATE NULL,
    visite_technique_expiration DATE NULL,
    statut VARCHAR(30) NOT NULL DEFAULT 'disponible',
    actif BOOLEAN NOT NULL DEFAULT true,
    created_by_id INTEGER NULL REFERENCES public.utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.trajets_transport (
    id SERIAL PRIMARY KEY,
    ville_depart VARCHAR(150) NOT NULL,
    destination VARCHAR(150) NOT NULL,
    axe_principal VARCHAR(255) NULL,
    type_trajet VARCHAR(50) NOT NULL DEFAULT 'aller_retour',
    distance_km NUMERIC(8, 2) NULL,
    duree_estimee_minutes INTEGER NULL,
    nombre_peages INTEGER NULL,
    notes TEXT NULL,
    actif BOOLEAN NOT NULL DEFAULT true,
    created_by_id INTEGER NULL REFERENCES public.utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.peages_transport (
    id SERIAL PRIMARY KEY,
    nom_poste VARCHAR(150) NOT NULL,
    axe VARCHAR(255) NULL,
    classe_vehicule VARCHAR(50) NULL,
    montant NUMERIC(12, 2) NOT NULL DEFAULT 0,
    date_application DATE NULL,
    source VARCHAR(255) NULL,
    actif BOOLEAN NOT NULL DEFAULT true,
    created_by_id INTEGER NULL REFERENCES public.utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS vehicule_id INTEGER NULL;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS trajet_id INTEGER NULL;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS mode_tarif VARCHAR(30) NOT NULL DEFAULT 'forfait';
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS distance_km NUMERIC(8, 2) NULL;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS classe_peage VARCHAR(50) NULL;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS montant_peage NUMERIC(12, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS montant_carburant NUMERIC(12, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS frais_chauffeur NUMERIC(12, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS frais_nuitee_chauffeur NUMERIC(12, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS frais_supplementaire NUMERIC(12, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS devise VARCHAR(10) NOT NULL DEFAULT 'XOF';
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS date_debut_validite DATE NULL;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS date_fin_validite DATE NULL;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS conditions TEXT NULL;
ALTER TABLE public.tarifs_transport ADD COLUMN IF NOT EXISTS statut VARCHAR(30) NOT NULL DEFAULT 'actif';

UPDATE public.tarifs_transport
SET
    mode_tarif = COALESCE(mode_tarif, 'forfait'),
    montant_peage = COALESCE(montant_peage, 0),
    montant_carburant = COALESCE(montant_carburant, 0),
    frais_chauffeur = COALESCE(frais_chauffeur, 0),
    frais_nuitee_chauffeur = COALESCE(frais_nuitee_chauffeur, 0),
    frais_supplementaire = COALESCE(frais_supplementaire, 0),
    devise = COALESCE(devise, 'XOF'),
    statut = COALESCE(statut, CASE WHEN actif IS FALSE THEN 'inactif' ELSE 'actif' END);

ALTER TABLE public.offre ALTER COLUMN montant_total SET DEFAULT 0;
UPDATE public.offre SET montant_total = 0 WHERE montant_total IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
        WHERE c.conrelid = 'public.tarifs_transport'::regclass
          AND c.contype = 'f'
          AND a.attname = 'vehicule_id'
    ) THEN
        ALTER TABLE public.tarifs_transport
        ADD CONSTRAINT fk_tarifs_transport_vehicule_id
        FOREIGN KEY (vehicule_id) REFERENCES public.vehicules_transport(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
        WHERE c.conrelid = 'public.tarifs_transport'::regclass
          AND c.contype = 'f'
          AND a.attname = 'trajet_id'
    ) THEN
        ALTER TABLE public.tarifs_transport
        ADD CONSTRAINT fk_tarifs_transport_trajet_id
        FOREIGN KEY (trajet_id) REFERENCES public.trajets_transport(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_vehicules_transport_nombre_places_pos') THEN
        ALTER TABLE public.vehicules_transport
        ADD CONSTRAINT ck_vehicules_transport_nombre_places_pos
        CHECK (nombre_places IS NULL OR nombre_places > 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_vehicules_transport_statut') THEN
        ALTER TABLE public.vehicules_transport
        ADD CONSTRAINT ck_vehicules_transport_statut
        CHECK (statut IN ('disponible','maintenance','indisponible','archive'));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_trajets_transport_distance_non_neg') THEN
        ALTER TABLE public.trajets_transport
        ADD CONSTRAINT ck_trajets_transport_distance_non_neg
        CHECK (distance_km IS NULL OR distance_km >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_trajets_transport_duree_non_neg') THEN
        ALTER TABLE public.trajets_transport
        ADD CONSTRAINT ck_trajets_transport_duree_non_neg
        CHECK (duree_estimee_minutes IS NULL OR duree_estimee_minutes >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_trajets_transport_nombre_peages_non_neg') THEN
        ALTER TABLE public.trajets_transport
        ADD CONSTRAINT ck_trajets_transport_nombre_peages_non_neg
        CHECK (nombre_peages IS NULL OR nombre_peages >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_peages_transport_montant_non_neg') THEN
        ALTER TABLE public.peages_transport
        ADD CONSTRAINT ck_peages_transport_montant_non_neg
        CHECK (montant >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_tarifs_transport_statut') THEN
        ALTER TABLE public.tarifs_transport
        ADD CONSTRAINT ck_tarifs_transport_statut
        CHECK (statut IN ('actif','a_confirmer','expire','inactif'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_vehicules_transport_fournisseur_id ON public.vehicules_transport(fournisseur_id);
CREATE INDEX IF NOT EXISTS ix_vehicules_transport_type_vehicule ON public.vehicules_transport(type_vehicule);
CREATE INDEX IF NOT EXISTS ix_vehicules_transport_actif ON public.vehicules_transport(actif);
CREATE INDEX IF NOT EXISTS ix_trajets_transport_ville_depart ON public.trajets_transport(ville_depart);
CREATE INDEX IF NOT EXISTS ix_trajets_transport_destination ON public.trajets_transport(destination);
CREATE INDEX IF NOT EXISTS ix_trajets_transport_actif ON public.trajets_transport(actif);
CREATE INDEX IF NOT EXISTS ix_peages_transport_nom_poste ON public.peages_transport(nom_poste);
CREATE INDEX IF NOT EXISTS ix_peages_transport_classe_vehicule ON public.peages_transport(classe_vehicule);
CREATE INDEX IF NOT EXISTS ix_peages_transport_actif ON public.peages_transport(actif);
CREATE INDEX IF NOT EXISTS ix_tarifs_transport_vehicule_id ON public.tarifs_transport(vehicule_id);
CREATE INDEX IF NOT EXISTS ix_tarifs_transport_trajet_id ON public.tarifs_transport(trajet_id);
CREATE INDEX IF NOT EXISTS ix_tarifs_transport_statut ON public.tarifs_transport(statut);
