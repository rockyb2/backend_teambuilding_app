-- Migration prod - dernieres modifications BDD
-- Ajouts: proformas securisee, factures, paiements, depenses multi-poles.
-- A lancer apres un backup de la vraie base.

BEGIN;

-- 1) Proformas: necessaire avant facture.proforma_id.
CREATE TABLE IF NOT EXISTS proformas (
    id SERIAL NOT NULL,
    reference VARCHAR(50) NOT NULL,
    pole VARCHAR(30) DEFAULT 'teambuilding' NOT NULL,
    demande_team_building_id INTEGER,
    offre_id INTEGER,
    demande_tourisme_id INTEGER,
    demande_tourisme_custom_id INTEGER,
    offre_tourisme_id INTEGER,
    site_id INTEGER,
    client VARCHAR(255) NOT NULL,
    nombre_personnes INTEGER NOT NULL,
    objet VARCHAR(255) NOT NULL,
    date_proforma DATE NOT NULL,
    date_evenement DATE,
    sections JSONB DEFAULT '[]'::jsonb NOT NULL,
    frais_agence NUMERIC(14, 2) DEFAULT 0 NOT NULL,
    details_frais_agence JSONB DEFAULT '[]'::jsonb NOT NULL,
    taux_tva_frais_agence NUMERIC(5, 2) DEFAULT 18 NOT NULL,
    sous_total_ht NUMERIC(14, 2) DEFAULT 0 NOT NULL,
    tva_frais_agence NUMERIC(14, 2) DEFAULT 0 NOT NULL,
    total_ttc NUMERIC(14, 2) DEFAULT 0 NOT NULL,
    modalite_paiement TEXT,
    recommandations JSONB DEFAULT '[]'::jsonb NOT NULL,
    notes TEXT,
    statut VARCHAR(30) DEFAULT 'brouillon' NOT NULL,
    fichier_pdf VARCHAR(500),
    created_by_id INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT ck_proformas_pole CHECK (pole IN ('teambuilding','tourisme')),
    CONSTRAINT ck_proformas_statut CHECK (statut IN ('brouillon','validee','pdf_genere','annulee')),
    CONSTRAINT ck_proformas_nombre_personnes_pos CHECK (nombre_personnes > 0),
    CONSTRAINT ck_proformas_sous_total_ht_non_negatif CHECK (sous_total_ht >= 0),
    CONSTRAINT ck_proformas_frais_agence_non_negatif CHECK (frais_agence >= 0),
    CONSTRAINT ck_proformas_tva_non_negatif CHECK (tva_frais_agence >= 0),
    CONSTRAINT ck_proformas_total_ttc_non_negatif CHECK (total_ttc >= 0),
    FOREIGN KEY(demande_team_building_id) REFERENCES demandes_team_building (id) ON DELETE SET NULL,
    FOREIGN KEY(offre_id) REFERENCES offre (id) ON DELETE SET NULL,
    FOREIGN KEY(demande_tourisme_id) REFERENCES demandes_tourisme (id) ON DELETE SET NULL,
    FOREIGN KEY(demande_tourisme_custom_id) REFERENCES demandes_tourisme_custom (id) ON DELETE SET NULL,
    FOREIGN KEY(offre_tourisme_id) REFERENCES offre_tourisme (id) ON DELETE SET NULL,
    FOREIGN KEY(site_id) REFERENCES site (id_site) ON DELETE SET NULL,
    FOREIGN KEY(created_by_id) REFERENCES utilisateur (id_utilisateur) ON DELETE SET NULL
);

ALTER TABLE proformas ADD COLUMN IF NOT EXISTS pole VARCHAR(30) NOT NULL DEFAULT 'teambuilding';
ALTER TABLE proformas ADD COLUMN IF NOT EXISTS demande_tourisme_id INTEGER NULL REFERENCES demandes_tourisme(id) ON DELETE SET NULL;
ALTER TABLE proformas ADD COLUMN IF NOT EXISTS demande_tourisme_custom_id INTEGER NULL REFERENCES demandes_tourisme_custom(id) ON DELETE SET NULL;
ALTER TABLE proformas ADD COLUMN IF NOT EXISTS offre_tourisme_id INTEGER NULL REFERENCES offre_tourisme(id) ON DELETE SET NULL;

UPDATE proformas
SET pole = 'teambuilding'
WHERE pole IS NULL OR pole NOT IN ('teambuilding', 'tourisme');

ALTER TABLE proformas ALTER COLUMN pole SET DEFAULT 'teambuilding';
ALTER TABLE proformas ALTER COLUMN pole SET NOT NULL;

ALTER TABLE proformas DROP CONSTRAINT IF EXISTS ck_proformas_pole;
ALTER TABLE proformas
ADD CONSTRAINT ck_proformas_pole
CHECK (pole IN ('teambuilding', 'tourisme'));

CREATE INDEX IF NOT EXISTS ix_proformas_demande_team_building_id ON proformas (demande_team_building_id);
CREATE INDEX IF NOT EXISTS ix_proformas_demande_tourisme_custom_id ON proformas (demande_tourisme_custom_id);
CREATE INDEX IF NOT EXISTS ix_proformas_demande_tourisme_id ON proformas (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_proformas_id ON proformas (id);
CREATE INDEX IF NOT EXISTS ix_proformas_offre_id ON proformas (offre_id);
CREATE INDEX IF NOT EXISTS ix_proformas_offre_tourisme_id ON proformas (offre_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_proformas_pole ON proformas (pole);
CREATE UNIQUE INDEX IF NOT EXISTS ix_proformas_reference ON proformas (reference);
CREATE INDEX IF NOT EXISTS ix_proformas_site_id ON proformas (site_id);

-- 2) Factures.
CREATE TABLE IF NOT EXISTS facture (
    id SERIAL PRIMARY KEY,
    reference_interne VARCHAR(50) NOT NULL UNIQUE,
    numero_fne VARCHAR(100) UNIQUE,
    pole VARCHAR(30) NOT NULL,
    proforma_id INTEGER NULL REFERENCES proformas(id) ON DELETE SET NULL,
    demande_team_building_id INTEGER NULL REFERENCES demandes_team_building(id) ON DELETE SET NULL,
    demande_tourisme_id INTEGER NULL REFERENCES demandes_tourisme(id) ON DELETE SET NULL,
    demande_tourisme_custom_id INTEGER NULL REFERENCES demandes_tourisme_custom(id) ON DELETE SET NULL,
    client VARCHAR(255) NOT NULL,
    objet VARCHAR(255),
    date_facture DATE NOT NULL DEFAULT CURRENT_DATE,
    montant_facture NUMERIC(14, 2) NOT NULL DEFAULT 0,
    statut VARCHAR(30) NOT NULL DEFAULT 'non_payee',
    created_by_id INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    updated_by_id INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_facture_pole CHECK (pole IN ('teambuilding', 'tourisme', 'production')),
    CONSTRAINT ck_facture_statut CHECK (statut IN ('non_payee', 'partiellement_payee', 'payee', 'annulee')),
    CONSTRAINT ck_facture_montant_non_negatif CHECK (montant_facture >= 0)
);

UPDATE facture
SET pole = 'teambuilding'
WHERE pole IS NULL OR pole NOT IN ('teambuilding', 'tourisme', 'production');

UPDATE facture
SET statut = 'non_payee'
WHERE statut IS NULL OR statut NOT IN ('non_payee', 'partiellement_payee', 'payee', 'annulee');

ALTER TABLE facture DROP CONSTRAINT IF EXISTS ck_facture_pole;
ALTER TABLE facture
ADD CONSTRAINT ck_facture_pole
CHECK (pole IN ('teambuilding', 'tourisme', 'production'));

ALTER TABLE facture DROP CONSTRAINT IF EXISTS ck_facture_statut;
ALTER TABLE facture
ADD CONSTRAINT ck_facture_statut
CHECK (statut IN ('non_payee', 'partiellement_payee', 'payee', 'annulee'));

ALTER TABLE facture DROP CONSTRAINT IF EXISTS ck_facture_montant_non_negatif;
ALTER TABLE facture
ADD CONSTRAINT ck_facture_montant_non_negatif
CHECK (montant_facture >= 0);

CREATE INDEX IF NOT EXISTS ix_facture_reference_interne ON facture (reference_interne);
CREATE INDEX IF NOT EXISTS ix_facture_numero_fne ON facture (numero_fne);
CREATE INDEX IF NOT EXISTS ix_facture_pole ON facture (pole);
CREATE INDEX IF NOT EXISTS ix_facture_statut ON facture (statut);
CREATE INDEX IF NOT EXISTS ix_facture_proforma_id ON facture (proforma_id);
CREATE INDEX IF NOT EXISTS ix_facture_demande_team_building_id ON facture (demande_team_building_id);
CREATE INDEX IF NOT EXISTS ix_facture_demande_tourisme_id ON facture (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_facture_demande_tourisme_custom_id ON facture (demande_tourisme_custom_id);

-- 3) Paiements.
CREATE TABLE IF NOT EXISTS paiement (
    id SERIAL PRIMARY KEY,
    facture_id INTEGER NOT NULL REFERENCES facture(id) ON DELETE CASCADE,
    montant NUMERIC(14, 2) NOT NULL,
    date_paiement DATE NOT NULL DEFAULT CURRENT_DATE,
    mode_paiement VARCHAR(50),
    reference_transaction VARCHAR(150),
    created_by_id INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    updated_by_id INTEGER NULL REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_paiement_montant_pos CHECK (montant > 0),
    CONSTRAINT ck_paiement_mode_paiement CHECK (
        mode_paiement IS NULL
        OR mode_paiement IN (
            'ESPECES',
            'WAVE',
            'ORANGE_MONEY',
            'MTN_MONEY',
            'VIREMENT',
            'CHEQUE',
            'CARTE_BANCAIRE'
        )
    )
);

ALTER TABLE paiement DROP CONSTRAINT IF EXISTS ck_paiement_montant_pos;
ALTER TABLE paiement
ADD CONSTRAINT ck_paiement_montant_pos
CHECK (montant > 0);

ALTER TABLE paiement DROP CONSTRAINT IF EXISTS ck_paiement_mode_paiement;
ALTER TABLE paiement
ADD CONSTRAINT ck_paiement_mode_paiement
CHECK (
    mode_paiement IS NULL
    OR mode_paiement IN (
        'ESPECES',
        'WAVE',
        'ORANGE_MONEY',
        'MTN_MONEY',
        'VIREMENT',
        'CHEQUE',
        'CARTE_BANCAIRE'
    )
);

CREATE INDEX IF NOT EXISTS ix_paiement_facture_id ON paiement (facture_id);

-- 4) Depenses: poles finance + liens vers proformas/factures/demandes.
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
WHERE pole IS NULL OR pole NOT IN ('teambuilding', 'tourisme', 'production');

ALTER TABLE depense ALTER COLUMN pole SET DEFAULT 'teambuilding';
ALTER TABLE depense ALTER COLUMN pole SET NOT NULL;

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

ALTER TABLE depense DROP CONSTRAINT IF EXISTS ck_depense_pole;
ALTER TABLE depense
ADD CONSTRAINT ck_depense_pole
CHECK (pole IN ('teambuilding', 'tourisme', 'production'));

-- Nettoyage des liens orphelins avant de remettre les cles etrangeres.
UPDATE facture f
SET proforma_id = NULL
WHERE proforma_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM proformas p WHERE p.id = f.proforma_id
  );

UPDATE depense d
SET proforma_id = NULL
WHERE proforma_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM proformas p WHERE p.id = d.proforma_id
  );

ALTER TABLE facture DROP CONSTRAINT IF EXISTS facture_proforma_id_fkey;
ALTER TABLE facture
ADD CONSTRAINT facture_proforma_id_fkey
FOREIGN KEY (proforma_id) REFERENCES proformas(id) ON DELETE SET NULL;

ALTER TABLE depense DROP CONSTRAINT IF EXISTS depense_activite_id_fkey;
ALTER TABLE depense
ADD CONSTRAINT depense_activite_id_fkey
FOREIGN KEY (activite_id) REFERENCES activite(id) ON DELETE SET NULL;

ALTER TABLE depense DROP CONSTRAINT IF EXISTS depense_proforma_id_fkey;
ALTER TABLE depense
ADD CONSTRAINT depense_proforma_id_fkey
FOREIGN KEY (proforma_id) REFERENCES proformas(id) ON DELETE SET NULL;

ALTER TABLE depense DROP CONSTRAINT IF EXISTS depense_facture_id_fkey;
ALTER TABLE depense
ADD CONSTRAINT depense_facture_id_fkey
FOREIGN KEY (facture_id) REFERENCES facture(id) ON DELETE SET NULL;

ALTER TABLE depense DROP CONSTRAINT IF EXISTS depense_demande_team_building_id_fkey;
ALTER TABLE depense
ADD CONSTRAINT depense_demande_team_building_id_fkey
FOREIGN KEY (demande_team_building_id) REFERENCES demandes_team_building(id) ON DELETE SET NULL;

ALTER TABLE depense DROP CONSTRAINT IF EXISTS depense_demande_tourisme_id_fkey;
ALTER TABLE depense
ADD CONSTRAINT depense_demande_tourisme_id_fkey
FOREIGN KEY (demande_tourisme_id) REFERENCES demandes_tourisme(id) ON DELETE SET NULL;

ALTER TABLE depense DROP CONSTRAINT IF EXISTS depense_demande_tourisme_custom_id_fkey;
ALTER TABLE depense
ADD CONSTRAINT depense_demande_tourisme_custom_id_fkey
FOREIGN KEY (demande_tourisme_custom_id) REFERENCES demandes_tourisme_custom(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_depense_pole ON depense (pole);
CREATE INDEX IF NOT EXISTS ix_depense_proforma_id ON depense (proforma_id);
CREATE INDEX IF NOT EXISTS ix_depense_facture_id ON depense (facture_id);
CREATE INDEX IF NOT EXISTS ix_depense_demande_team_building_id ON depense (demande_team_building_id);
CREATE INDEX IF NOT EXISTS ix_depense_demande_tourisme_id ON depense (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_depense_demande_tourisme_custom_id ON depense (demande_tourisme_custom_id);

COMMIT;

-- Verification rapide apres execution:
-- SELECT to_regclass('public.proformas') AS proformas,
--        to_regclass('public.facture') AS facture,
--        to_regclass('public.paiement') AS paiement;
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name IN ('facture', 'paiement', 'depense')
-- ORDER BY table_name, ordinal_position;
