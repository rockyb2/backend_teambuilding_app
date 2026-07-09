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

CREATE INDEX IF NOT EXISTS ix_facture_reference_interne ON facture (reference_interne);
CREATE INDEX IF NOT EXISTS ix_facture_numero_fne ON facture (numero_fne);
CREATE INDEX IF NOT EXISTS ix_facture_pole ON facture (pole);
CREATE INDEX IF NOT EXISTS ix_facture_statut ON facture (statut);
CREATE INDEX IF NOT EXISTS ix_facture_proforma_id ON facture (proforma_id);
CREATE INDEX IF NOT EXISTS ix_facture_demande_team_building_id ON facture (demande_team_building_id);
CREATE INDEX IF NOT EXISTS ix_facture_demande_tourisme_id ON facture (demande_tourisme_id);
CREATE INDEX IF NOT EXISTS ix_facture_demande_tourisme_custom_id ON facture (demande_tourisme_custom_id);
CREATE INDEX IF NOT EXISTS ix_paiement_facture_id ON paiement (facture_id);
