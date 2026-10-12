CREATE TABLE IF NOT EXISTS taxes (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    type_calcul VARCHAR(30) NOT NULL CHECK (type_calcul IN ('pourcentage', 'pourcentage_lignes', 'forfait_chambre_nuit')),
    taux NUMERIC(7,4),
    bareme JSONB NOT NULL DEFAULT '[]'::jsonb,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
ALTER TABLE proformas ADD COLUMN IF NOT EXISTS taxes_selectionnees JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE proformas ADD COLUMN IF NOT EXISTS nombre_nuitees INTEGER NOT NULL DEFAULT 0;
ALTER TABLE proformas ADD COLUMN IF NOT EXISTS nombre_chambres INTEGER NOT NULL DEFAULT 0;
ALTER TABLE proformas ADD COLUMN IF NOT EXISTS total_taxes NUMERIC(14,2) NOT NULL DEFAULT 0;
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS taxes_selectionnees JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS nombre_nuitees INTEGER NOT NULL DEFAULT 0;
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS nombre_chambres INTEGER NOT NULL DEFAULT 0;
ALTER TABLE budgets ADD COLUMN IF NOT EXISTS total_taxes NUMERIC(14,2) NOT NULL DEFAULT 0;
INSERT INTO taxes (nom, code, type_calcul, taux, bareme, description)
VALUES
 ('Taxe de développement touristique', 'TDT', 'pourcentage', 2.5, '[]'::jsonb, 'Calculée sur le montant hors taxes'),
 ('Taxe communale de nuitée', 'NUITEE', 'forfait_chambre_nuit', NULL,
  '[{"label":"Tarif 500 FCFA","amount":500},{"label":"Tarif 1000 FCFA","amount":1000},{"label":"Tarif 1500 FCFA","amount":1500},{"label":"Tarif 2000 FCFA","amount":2000}]'::jsonb,
  'Calculée par chambre et par nuitée')
ON CONFLICT (code) DO NOTHING;
