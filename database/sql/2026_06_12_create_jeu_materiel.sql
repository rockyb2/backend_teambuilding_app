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
