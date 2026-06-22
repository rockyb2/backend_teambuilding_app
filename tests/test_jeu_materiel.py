import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from core.env_loader import load_local_env

load_local_env()

from api.jeux.routes import _validate_materiels_requis
from crud.jeu import _build_materiel_associations, _sync_materiel_associations
from database.models import Jeu
from database.schemas import JeuCreate, JeuUpdate


class JeuMaterielTests(unittest.TestCase):
    def test_create_contract_accepts_material_quantities(self):
        payload = JeuCreate(
            nom_jeu="Relais",
            materiels=[
                {"materiel_id": 4, "quantite_requise": 2},
                {"materiel_id": 8, "quantite_requise": 5},
            ],
        )

        self.assertEqual(len(payload.materiels), 2)
        self.assertEqual(payload.materiels[0].quantite_requise, 2)

    def test_update_contract_distinguishes_omitted_and_empty_materials(self):
        omitted = JeuUpdate(nom_jeu="Relais")
        emptied = JeuUpdate(materiels=[])

        self.assertNotIn("materiels", omitted.model_dump(exclude_unset=True))
        self.assertEqual(emptied.model_dump(exclude_unset=True)["materiels"], [])

    def test_material_associations_are_deduplicated(self):
        associations = _build_materiel_associations(
            [
                {"materiel_id": 4, "quantite_requise": 2},
                {"materiel_id": 4, "quantite_requise": 3},
            ]
        )

        self.assertEqual(len(associations), 1)
        self.assertEqual(associations[0].materiel_id, 4)
        self.assertEqual(associations[0].quantite_requise, 3)

    def test_sync_updates_existing_association_without_duplicate(self):
        jeu = Jeu(nom_jeu="Relais")
        jeu.materiels = _build_materiel_associations(
            [{"materiel_id": 4, "quantite_requise": 2}]
        )

        _sync_materiel_associations(
            jeu,
            [{"materiel_id": 4, "quantite_requise": 5}],
        )

        self.assertEqual(len(jeu.materiels), 1)
        self.assertEqual(jeu.materiels[0].quantite_requise, 5)

    @patch("api.jeux.routes.crud_materiel.get_materiel")
    def test_game_required_quantity_cannot_exceed_stock_total(self, get_materiel_mock):
        get_materiel_mock.return_value = SimpleNamespace(
            nom="Cerceau",
            quantite_disponible=3,
            statut=True,
        )

        with self.assertRaises(HTTPException) as raised:
            _validate_materiels_requis(
                Mock(),
                [{"materiel_id": 7, "quantite_requise": 4}],
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("3 unite(s)", raised.exception.detail)

    @patch("api.jeux.routes.crud_materiel.get_materiel")
    def test_game_required_quantity_accepts_available_stock_total(self, get_materiel_mock):
        get_materiel_mock.return_value = SimpleNamespace(
            nom="Cerceau",
            quantite_disponible=3,
            statut=True,
        )

        _validate_materiels_requis(
            Mock(),
            [{"materiel_id": 7, "quantite_requise": 3}],
        )

    @patch("api.jeux.routes.crud_materiel.get_materiel")
    def test_game_cannot_require_inactive_material(self, get_materiel_mock):
        get_materiel_mock.return_value = SimpleNamespace(
            nom="Cerceau",
            quantite_disponible=3,
            statut=False,
        )

        with self.assertRaises(HTTPException) as raised:
            _validate_materiels_requis(
                Mock(),
                [{"materiel_id": 7, "quantite_requise": 1}],
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("Materiel inactif", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
