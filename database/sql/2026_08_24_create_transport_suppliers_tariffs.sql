CREATE TABLE IF NOT EXISTS fournisseurs_transport (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    telephone VARCHAR(50),
    email VARCHAR(150),
    localisation VARCHAR(150),
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_fournisseurs_transport_nom'
    ) THEN
        ALTER TABLE fournisseurs_transport
        ADD CONSTRAINT uq_fournisseurs_transport_nom UNIQUE (nom);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS tarifs_transport (
    id SERIAL PRIMARY KEY,
    fournisseur_id INTEGER NOT NULL REFERENCES fournisseurs_transport(id) ON DELETE CASCADE,
    type_transport VARCHAR(50) NOT NULL,
    libelle VARCHAR(255) NOT NULL,
    nombre_places INTEGER,
    climatisation BOOLEAN NOT NULL DEFAULT FALSE,
    chauffeur_inclus BOOLEAN NOT NULL DEFAULT TRUE,
    carburant_inclus BOOLEAN NOT NULL DEFAULT FALSE,
    peage_inclus BOOLEAN NOT NULL DEFAULT FALSE,
    unite_tarif VARCHAR(30) NOT NULL DEFAULT 'jour',
    prix_unitaire NUMERIC(12, 2) NOT NULL DEFAULT 0,
    zone_depart VARCHAR(150),
    destination VARCHAR(150),
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_id INTEGER REFERENCES utilisateur(id_utilisateur) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_tarifs_transport_nombre_places_pos
        CHECK (nombre_places IS NULL OR nombre_places > 0),
    CONSTRAINT ck_tarifs_transport_prix_unitaire_non_neg
        CHECK (prix_unitaire >= 0)
);

CREATE INDEX IF NOT EXISTS ix_fournisseurs_transport_actif
    ON fournisseurs_transport(actif);

CREATE INDEX IF NOT EXISTS ix_fournisseurs_transport_created_by_id
    ON fournisseurs_transport(created_by_id);

CREATE INDEX IF NOT EXISTS ix_tarifs_transport_fournisseur_id
    ON tarifs_transport(fournisseur_id);

CREATE INDEX IF NOT EXISTS ix_tarifs_transport_type_transport
    ON tarifs_transport(type_transport);

CREATE INDEX IF NOT EXISTS ix_tarifs_transport_actif
    ON tarifs_transport(actif);

CREATE INDEX IF NOT EXISTS ix_tarifs_transport_created_by_id
    ON tarifs_transport(created_by_id);
