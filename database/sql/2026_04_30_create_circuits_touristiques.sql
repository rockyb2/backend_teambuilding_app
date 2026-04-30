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
