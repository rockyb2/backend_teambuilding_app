BEGIN;

ALTER TABLE public.demandes_team_building
ADD COLUMN IF NOT EXISTS date_demande DATE;

UPDATE public.demandes_team_building
SET date_demande = COALESCE(date_demande, created_at::date, CURRENT_DATE)
WHERE date_demande IS NULL;

ALTER TABLE public.demandes_team_building
ALTER COLUMN date_demande SET DEFAULT CURRENT_DATE,
ALTER COLUMN date_demande SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_demandes_team_building_date_demande
ON public.demandes_team_building (date_demande);

COMMIT;
