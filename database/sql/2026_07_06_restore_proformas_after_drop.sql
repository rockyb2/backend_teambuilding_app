-- Restauration de la table proformas apres un DROP ... CASCADE accidentel.
-- Attention : les anciennes lignes de proformas supprimees ne peuvent pas etre recuperees
-- par ce script. Il restaure uniquement la structure et les contraintes.

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

CREATE INDEX IF NOT EXISTS ix_proformas_demande_team_building_id ON proformas (demande_team_building_id);
CREATE INDEX IF NOT EXISTS ix_proformas_demande_tourisme_custom_id ON proformas (demande_tourisme_custom_id);
CREATE INDEX IF NOT EXISTS ix_proformas_demande_tourisme_id ON proformas (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_proformas_id ON proformas (id);
CREATE INDEX IF NOT EXISTS ix_proformas_offre_id ON proformas (offre_id);
CREATE INDEX IF NOT EXISTS ix_proformas_offre_tourisme_id ON proformas (offre_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_proformas_pole ON proformas (pole);
CREATE UNIQUE INDEX IF NOT EXISTS ix_proformas_reference ON proformas (reference);
CREATE INDEX IF NOT EXISTS ix_proformas_site_id ON proformas (site_id);

-- DROP ... CASCADE supprime aussi les contraintes qui pointaient vers proformas.
-- Les anciennes valeurs de proforma_id deviennent orphelines puisque les anciennes proformas
-- n'existent plus ; on les nettoie avant de remettre les cles etrangeres.
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

ALTER TABLE facture
DROP CONSTRAINT IF EXISTS facture_proforma_id_fkey;

ALTER TABLE facture
ADD CONSTRAINT facture_proforma_id_fkey
FOREIGN KEY (proforma_id) REFERENCES proformas(id) ON DELETE SET NULL;

ALTER TABLE depense
DROP CONSTRAINT IF EXISTS depense_proforma_id_fkey;

ALTER TABLE depense
ADD CONSTRAINT depense_proforma_id_fkey
FOREIGN KEY (proforma_id) REFERENCES proformas(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_facture_proforma_id ON facture (proforma_id);
CREATE INDEX IF NOT EXISTS ix_depense_proforma_id ON depense (proforma_id);
