BEGIN;

-- PostgreSQL distingue SQL NULL de la valeur JSONB "null".
-- Les contraintes des tarifs autorisent SQL NULL ou un objet JSON.
UPDATE public.site
SET tarifs_restauration = NULL
WHERE tarifs_restauration = 'null'::jsonb;

UPDATE public.site
SET tarifs_seminaire = NULL
WHERE tarifs_seminaire = 'null'::jsonb;

COMMIT;
