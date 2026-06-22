import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from core.env_loader import load_local_env

load_local_env()

from services.proforma_assistant import (
    create_assistant_session,
    handle_assistant_message,
    search_best_sites,
)
from services.proforma_pdf import calculate_totals, generate_proforma_pdf


class ProformaAssistantTests(unittest.TestCase):
    def build_db_with_sites(self, sites):
        db = Mock()
        query = Mock()
        db.query.return_value = query
        query.all.return_value = sites
        return db

    def test_site_scoring_prioritizes_capacity_room_food_and_budget(self):
        good_site = SimpleNamespace(
            id_site=1,
            nom_site="Songon Park",
            localisation="Songon",
            capacite=80,
            type_site="plein air",
            a_salle_seminaire=True,
            tarifs_seminaire={"journee": 250000},
            a_restauration=True,
            tarifs_restauration={"pause_cafe": 5000, "dejeuner": 12000},
        )
        weak_site = SimpleNamespace(
            id_site=2,
            nom_site="Petit Espace",
            localisation="Cocody",
            capacite=20,
            type_site="interieur",
            a_salle_seminaire=False,
            tarifs_seminaire=None,
            a_restauration=False,
            tarifs_restauration=None,
        )
        fields = {
            "nombre_personnes": 50,
            "lieu_souhaite": "Songon",
            "budget_estime": 1500000,
            "avec_salle": True,
            "restauration_incluse": True,
        }

        recommendations = search_best_sites(self.build_db_with_sites([weak_site, good_site]), fields)

        self.assertEqual(recommendations[0]["site_id"], 1)
        self.assertGreater(recommendations[0]["score"], recommendations[1]["score"])
        self.assertTrue(recommendations[1]["warnings"])

    def test_calculate_totals_includes_agency_vat(self):
        totals = calculate_totals(
            [
                {
                    "nom": "Site",
                    "prestations": [
                        {"designation": "Salle", "quantite": 1, "prix_unitaire": 250000},
                        {"designation": "Dejeuner", "quantite": 50, "prix_unitaire": 12000},
                    ],
                }
            ],
            frais_agence=150000,
            taux_tva_frais_agence=18,
        )

        self.assertEqual(int(totals["sous_total_ht"]), 850000)
        self.assertEqual(int(totals["tva_frais_agence"]), 27000)
        self.assertEqual(int(totals["total_ttc"]), 1027000)

    def test_generate_pdf_creates_file(self):
        data = {
            "reference": "PRO-2026-0001",
            "client": "Client Test",
            "nombre_personnes": 20,
            "date_proforma": "16/06/2026",
            "objet": "Team building",
            "sections": [
                {
                    "nom": "Site",
                    "prestations": [
                        {"designation": "Salle", "quantite": 1, "prix_unitaire": 100000},
                    ],
                }
            ],
            "frais_agence": 150000,
            "taux_tva_frais_agence": 18,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = generate_proforma_pdf(data, output_dir=temp_dir)
            self.assertTrue(path.endswith(".pdf"))

    def test_sessions_are_isolated_by_user(self):
        session = create_assistant_session(Mock(), user_id=10)

        with self.assertRaises(PermissionError):
            handle_assistant_message(
                Mock(),
                session_id=session["session_id"],
                message="client: Test, 30 personnes",
                user_id=11,
            )


if __name__ == "__main__":
    unittest.main()
