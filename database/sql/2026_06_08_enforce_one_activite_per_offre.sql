-- Une offre correspond a une seule activite Team Building.
-- L'offre peut exister avant la planification, mais ne peut pas etre reutilisee.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.activite'::regclass
          AND conname = 'activite_id_offre_key'
    ) THEN
        ALTER TABLE public.activite
        ADD CONSTRAINT activite_id_offre_key UNIQUE (offre_id);
    END IF;
END
$$;

-- La contrainte UNIQUE cree deja son propre index.
DROP INDEX IF EXISTS public.ix_activite_offre_id;
