ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS mode_frais_agence VARCHAR(20) NOT NULL DEFAULT 'montant';
ALTER TABLE public.proformas ADD COLUMN IF NOT EXISTS mode_frais_agence VARCHAR(20);
