BEGIN;

-- Convertit les anciennes valeurs avant de remplacer la contrainte.
UPDATE public.offre
SET statut = CASE statut
    WHEN 'envoye' THEN 'envoyee'
    WHEN 'valide' THEN 'validee'
    WHEN 'refuse' THEN 'refusee'
    WHEN 'expire' THEN 'expiree'
    WHEN 'annule' THEN 'annulee'
    ELSE statut
END
WHERE statut IN ('envoye', 'valide', 'refuse', 'expire', 'annule');

ALTER TABLE public.offre
DROP CONSTRAINT IF EXISTS ck_offre_statut;

ALTER TABLE public.offre
ADD CONSTRAINT ck_offre_statut
CHECK (
    statut IN (
        'brouillon',
        'envoyee',
        'validee',
        'refusee',
        'expiree',
        'annulee'
    )
);

COMMIT;
