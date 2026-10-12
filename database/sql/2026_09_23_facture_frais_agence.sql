-- Executed by create_tables at startup; safe to run again on PostgreSQL.
ALTER TABLE facture ADD COLUMN IF NOT EXISTS frais_agence NUMERIC(14, 2) NULL;
ALTER TABLE facture ADD COLUMN IF NOT EXISTS proforma_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE depense ADD COLUMN IF NOT EXISTS facture_ligne_cle VARCHAR(80) NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_facture_frais_agence_non_negatif'
          AND conrelid = 'facture'::regclass
    ) THEN
        ALTER TABLE facture ADD CONSTRAINT ck_facture_frais_agence_non_negatif
            CHECK (frais_agence IS NULL OR frais_agence >= 0);
    END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_depense_ligne_facture_requiert_facture'
          AND conrelid = 'depense'::regclass
    ) THEN
        ALTER TABLE depense ADD CONSTRAINT ck_depense_ligne_facture_requiert_facture
            CHECK (facture_ligne_cle IS NULL OR facture_id IS NOT NULL);
    END IF;
END;
$$;

-- Preserve existing amounts. Unknown manual invoices remain NULL, not zero.
-- Do not multiply the agency fee for legacy duplicate invoices on a proforma.
UPDATE facture AS f
SET frais_agence = p.frais_agence
FROM proformas AS p
WHERE f.proforma_id = p.id
  AND f.pole = p.pole
  AND f.frais_agence IS NULL
  AND (
      SELECT COUNT(*) FROM facture AS other
      WHERE other.proforma_id = p.id AND other.statut <> 'annulee'
  ) <= 1;

-- Existing invoices receive the current proforma as their initial historical
-- snapshot. New invoices store the snapshot directly when they are created.
UPDATE facture AS f
SET proforma_snapshot = jsonb_build_object(
    'reference', p.reference,
    'date_proforma', p.date_proforma,
    'sections', p.sections,
    'sous_total_ht', p.sous_total_ht,
    'frais_agence', p.frais_agence,
    'tva_frais_agence', p.tva_frais_agence,
    'total_ttc', p.total_ttc
)
FROM proformas AS p
WHERE f.proforma_id = p.id
  AND (f.proforma_snapshot IS NULL OR f.proforma_snapshot = '{}'::jsonb);

CREATE INDEX IF NOT EXISTS ix_depense_facture_ligne_cle ON depense (facture_ligne_cle);
