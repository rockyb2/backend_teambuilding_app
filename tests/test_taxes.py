from decimal import Decimal
from types import SimpleNamespace
import unittest

from core.env_loader import load_local_env
from services.taxes import add_persisted_taxes, calculate_taxes

load_local_env()


class _Query:
    def __init__(self, taxes):
        self.taxes = taxes
        self.criteria = ()

    def filter(self, *criteria):
        self.criteria = criteria
        return self

    def first(self):
        # calculate_taxes performs one query per requested code, in selection order.
        return self.taxes.pop(0) if self.taxes else None


class _Db:
    def __init__(self, taxes):
        self.taxes = list(taxes)

    def query(self, _model):
        return _Query(self.taxes)


class TaxCalculationTests(unittest.TestCase):
    def test_tdt_and_night_tax_are_added(self):
        db = _Db([
            SimpleNamespace(id=1, code="TDT", nom="TDT", type_calcul="pourcentage", taux=Decimal("2.5"), bareme=[]),
            SimpleNamespace(id=2, code="NUITEE", nom="Nuitée", type_calcul="forfait_chambre_nuit", taux=None, bareme=[]),
        ])
        details, total = calculate_taxes(
            db,
            [{"code": "TDT"}, {"code": "NUITEE", "tarif": 1500}],
            300000,
            2,
            3,
        )
        self.assertEqual(total, Decimal("16500.00"))
        self.assertEqual(details[0]["montant"], 7500.0)
        self.assertEqual(details[1]["montant"], 9000.0)
        self.assertEqual(details[1]["tarif"], 1500.0)
        self.assertEqual(details[1]["nombre_chambres"], 2)

    def test_document_total_uses_persisted_tax_snapshot(self):
        totals = add_persisted_taxes(
            {"total_ttc": Decimal("300000")},
            {"taxes_selectionnees": [{"code": "TDT", "montant": 7500}, {"code": "NUITEE", "montant": 9000}]},
        )
        self.assertEqual(totals["total_taxes"], Decimal("16500.00"))
        self.assertEqual(totals["total_ttc"], Decimal("316500.00"))

    def test_hotel_vat_only_uses_marked_hotel_lines(self):
        db = _Db([
            SimpleNamespace(
                id=3,
                code="TVA_HOTEL",
                nom="TVA hôtel",
                type_calcul="pourcentage_lignes",
                taux=Decimal("18"),
                bareme=[],
            ),
        ])
        sections = [
            {
                "nom": "Prestations",
                "prestations": [
                    {"designation": "Hébergement", "montant_ht": 100000, "prestation_hoteliere": True},
                    {"designation": "Transport", "montant_ht": 50000, "prestation_hoteliere": False},
                ],
            },
        ]

        details, total = calculate_taxes(
            db,
            [{"code": "TVA_HOTEL"}],
            150000,
            0,
            0,
            sections,
        )

        self.assertEqual(total, Decimal("18000.00"))
        self.assertEqual(details[0]["base_ht"], 100000.0)
        self.assertEqual(details[0]["montant"], 18000.0)


if __name__ == "__main__":
    unittest.main()
