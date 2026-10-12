ALTER TABLE taxes DROP CONSTRAINT IF EXISTS taxes_type_calcul_check;
ALTER TABLE taxes
ADD CONSTRAINT taxes_type_calcul_check
CHECK (type_calcul IN ('pourcentage', 'pourcentage_lignes', 'forfait_chambre_nuit'));

INSERT INTO taxes (nom, code, type_calcul, taux, bareme, description)
VALUES (
    'TVA sur prestations hôtelières',
    'TVA_HOTEL',
    'pourcentage_lignes',
    18,
    '[]'::jsonb,
    'Calculée uniquement sur les prestations fournies par l’hôtel et exprimées hors taxes'
)
ON CONFLICT (code) DO UPDATE SET
    nom = EXCLUDED.nom,
    type_calcul = EXCLUDED.type_calcul,
    taux = EXCLUDED.taux,
    bareme = EXCLUDED.bareme,
    description = EXCLUDED.description;
