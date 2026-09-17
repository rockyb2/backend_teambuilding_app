ALTER TABLE public.budgets ADD COLUMN IF NOT EXISTS groupe_reference VARCHAR(50);
ALTER TABLE public.proformas ADD COLUMN IF NOT EXISTS budget_id INTEGER REFERENCES public.budgets(id) ON DELETE RESTRICT;
ALTER TABLE public.proformas ADD COLUMN IF NOT EXISTS budget_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb;

-- Conflicting historical approvals require a new explicit choice.
WITH conflicts AS (
    SELECT offre_id FROM public.budgets WHERE statut = 'valide'
    GROUP BY offre_id HAVING COUNT(*) > 1
), unvalidated AS (
    UPDATE public.budgets SET statut = 'genere', updated_at = CURRENT_TIMESTAMP
    WHERE statut = 'valide' AND offre_id IN (SELECT offre_id FROM conflicts)
    RETURNING offre_id
)
UPDATE public.offre SET montant_total = 0
WHERE id IN (SELECT offre_id FROM unvalidated);

CREATE UNIQUE INDEX IF NOT EXISTS uq_budgets_offre_valide ON public.budgets(offre_id) WHERE statut = 'valide';
CREATE INDEX IF NOT EXISTS ix_budgets_groupe_reference ON public.budgets(groupe_reference);
CREATE INDEX IF NOT EXISTS ix_proformas_budget_id ON public.proformas(budget_id);
