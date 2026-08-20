BEGIN;

ALTER TABLE public.demandes_tourisme
ADD COLUMN IF NOT EXISTS date_demande DATE;

ALTER TABLE public.demandes_tourisme_custom
ADD COLUMN IF NOT EXISTS date_demande DATE;

ALTER TABLE public.demandes_tourisme_custom
ADD COLUMN IF NOT EXISTS date_depart_souhaitee DATE;

UPDATE public.demandes_tourisme
SET date_demande = COALESCE(date_demande, created_at::date, CURRENT_DATE)
WHERE date_demande IS NULL;

UPDATE public.demandes_tourisme_custom
SET date_demande = COALESCE(date_demande, created_at::date, CURRENT_DATE)
WHERE date_demande IS NULL;

ALTER TABLE public.demandes_tourisme
ALTER COLUMN date_demande SET DEFAULT CURRENT_DATE,
ALTER COLUMN date_demande SET NOT NULL;

ALTER TABLE public.demandes_tourisme_custom
ALTER COLUMN date_demande SET DEFAULT CURRENT_DATE,
ALTER COLUMN date_demande SET NOT NULL;

ALTER TABLE public.demandes_tourisme_custom
ALTER COLUMN numero_telephone_client DROP NOT NULL;

CREATE INDEX IF NOT EXISTS ix_demandes_tourisme_date_demande
ON public.demandes_tourisme (date_demande);

CREATE INDEX IF NOT EXISTS ix_demandes_tourisme_custom_date_demande
ON public.demandes_tourisme_custom (date_demande);

CREATE INDEX IF NOT EXISTS ix_demandes_tourisme_custom_date_depart_souhaitee
ON public.demandes_tourisme_custom (date_depart_souhaitee);

COMMIT;
