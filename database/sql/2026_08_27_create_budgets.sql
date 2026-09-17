-- Création de la fonctionnalité budgets estimatifs liés aux offres.
-- Script idempotent pour PostgreSQL.

CREATE TABLE IF NOT EXISTS public.budgets (
    id SERIAL PRIMARY KEY,
    reference VARCHAR(50) NOT NULL UNIQUE,
    offre_id INTEGER NOT NULL REFERENCES public.offre(id) ON DELETE CASCADE,
    demande_team_building_id INTEGER NULL REFERENCES public.demandes_team_building(id) ON DELETE SET NULL,
    site_id INTEGER NULL REFERENCES public.site(id_site) ON DELETE SET NULL,
    titre VARCHAR(255) NOT NULL,
    client VARCHAR(255) NOT NULL,
    nombre_personnes INTEGER NOT NULL,
    date_budget DATE NOT NULL DEFAULT CURRENT_DATE,
    date_evenement DATE NULL,
    duree_jours INTEGER NULL,
    devise VARCHAR(10) NOT NULL DEFAULT 'XOF',
    sections JSONB NOT NULL DEFAULT '[]'::jsonb,
    options_selectionnees JSONB NOT NULL DEFAULT '{}'::jsonb,
    frais_agence NUMERIC(14, 2) NOT NULL DEFAULT 0,
    taux_tva_frais_agence NUMERIC(5, 2) NOT NULL DEFAULT 0,
    sous_total_ht NUMERIC(14, 2) NOT NULL DEFAULT 0,
    tva_frais_agence NUMERIC(14, 2) NOT NULL DEFAULT 0,
    total_ht NUMERIC(14, 2) NOT NULL DEFAULT 0,
    total_ttc NUMERIC(14, 2) NOT NULL DEFAULT 0,
    modalite_paiement TEXT NULL,
    notes TEXT NULL,
    statut VARCHAR(30) NOT NULL DEFAULT 'brouillon',
    fichier_pdf VARCHAR(500) NULL,
    fichier_excel VARCHAR(500) NULL,
    created_by_id INTEGER NULL REFERENCES public.utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
);

ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS demande_team_building_id INTEGER NULL REFERENCES public.demandes_team_building(id) ON DELETE SET NULL;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS site_id INTEGER NULL REFERENCES public.site(id_site) ON DELETE SET NULL;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS duree_jours INTEGER NULL;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS devise VARCHAR(10) NOT NULL DEFAULT 'XOF';
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS options_selectionnees JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS frais_agence NUMERIC(14, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS taux_tva_frais_agence NUMERIC(5, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS sous_total_ht NUMERIC(14, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS tva_frais_agence NUMERIC(14, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS total_ht NUMERIC(14, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS total_ttc NUMERIC(14, 2) NOT NULL DEFAULT 0;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS fichier_pdf VARCHAR(500) NULL;
ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS fichier_excel VARCHAR(500) NULL;

UPDATE public.budgets
SET
    date_budget = COALESCE(date_budget, CURRENT_DATE),
    sections = COALESCE(sections, '[]'::jsonb),
    options_selectionnees = COALESCE(options_selectionnees, '{}'::jsonb),
    frais_agence = COALESCE(frais_agence, 0),
    taux_tva_frais_agence = COALESCE(taux_tva_frais_agence, 0),
    sous_total_ht = COALESCE(sous_total_ht, 0),
    tva_frais_agence = COALESCE(tva_frais_agence, 0),
    total_ht = COALESCE(total_ht, 0),
    total_ttc = COALESCE(total_ttc, 0),
    devise = COALESCE(devise, 'XOF'),
    statut = COALESCE(statut, 'brouillon');

ALTER TABLE public.offre ALTER COLUMN montant_total SET DEFAULT 0;
UPDATE public.offre SET montant_total = 0 WHERE montant_total IS NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_budgets_statut') THEN
        ALTER TABLE public.budgets
        ADD CONSTRAINT ck_budgets_statut
        CHECK (statut IN ('brouillon','genere','valide','annule'));
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_budgets_nombre_personnes_pos') THEN
        ALTER TABLE public.budgets
        ADD CONSTRAINT ck_budgets_nombre_personnes_pos
        CHECK (nombre_personnes > 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_budgets_duree_jours_pos') THEN
        ALTER TABLE public.budgets
        ADD CONSTRAINT ck_budgets_duree_jours_pos
        CHECK (duree_jours IS NULL OR duree_jours > 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_budgets_sous_total_ht_non_neg') THEN
        ALTER TABLE public.budgets
        ADD CONSTRAINT ck_budgets_sous_total_ht_non_neg
        CHECK (sous_total_ht >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_budgets_frais_agence_non_neg') THEN
        ALTER TABLE public.budgets
        ADD CONSTRAINT ck_budgets_frais_agence_non_neg
        CHECK (frais_agence >= 0);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_budgets_total_ttc_non_neg') THEN
        ALTER TABLE public.budgets
        ADD CONSTRAINT ck_budgets_total_ttc_non_neg
        CHECK (total_ttc >= 0);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_budgets_reference ON public.budgets(reference);
CREATE INDEX IF NOT EXISTS ix_budgets_offre_id ON public.budgets(offre_id);
CREATE INDEX IF NOT EXISTS ix_budgets_demande_team_building_id ON public.budgets(demande_team_building_id);
CREATE INDEX IF NOT EXISTS ix_budgets_site_id ON public.budgets(site_id);
CREATE INDEX IF NOT EXISTS ix_budgets_statut ON public.budgets(statut);
CREATE INDEX IF NOT EXISTS ix_budgets_date_budget ON public.budgets(date_budget);
