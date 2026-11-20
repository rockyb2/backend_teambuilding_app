UPDATE taxes
SET
    type_calcul = 'pourcentage_lignes',
    taux = 2.5,
    description = 'Taxe fournisseur calculée sur les prestations hôtelières hors taxes',
    updated_at = NOW()
WHERE code = 'TDT';
