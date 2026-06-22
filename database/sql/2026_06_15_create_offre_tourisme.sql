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
