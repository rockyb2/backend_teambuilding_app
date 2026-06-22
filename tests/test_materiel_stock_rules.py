import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from core.env_loader import load_local_env

load_local_env()

from api.activites_materiels.routes import _validate_materiel_actif
from api.materiels.routes import _validate_stock_total_supports_reservations


class MaterielStockRulesTests(unittest.TestCase):
    @patch("api.materiels.routes.crud_activite_materiel.get_max_quantite_reservee")
    @patch("api.materiels.routes.crud_activite_materiel.lock_materiel_reservation")
    def test_stock_total_cannot_go_below_existing_reservations(self, lock_mock, max_reserved_mock):
        max_reserved_mock.return_value = 4

        with self.assertRaises(HTTPException) as raised:
            _validate_stock_total_supports_reservations(
                Mock(),
                materiel_id=12,
                updates={"quantite_disponible": 3},
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("4 unite(s)", raised.exception.detail)
        lock_mock.assert_called_once()

    @patch("api.materiels.routes.crud_activite_materiel.get_max_quantite_reservee")
    @patch("api.materiels.routes.crud_activite_materiel.lock_materiel_reservation")
    def test_stock_total_accepts_quantity_covering_reservations(self, lock_mock, max_reserved_mock):
        max_reserved_mock.return_value = 4

        _validate_stock_total_supports_reservations(
            Mock(),
            materiel_id=12,
            updates={"quantite_disponible": 4},
        )

        lock_mock.assert_called_once()

    @patch("api.materiels.routes.crud_activite_materiel.get_max_quantite_reservee")
    @patch("api.materiels.routes.crud_activite_materiel.lock_materiel_reservation")
    def test_stock_total_validation_ignores_unrelated_updates(self, lock_mock, max_reserved_mock):
        _validate_stock_total_supports_reservations(
            Mock(),
            materiel_id=12,
            updates={"description": "Kit animation"},
        )

        lock_mock.assert_not_called()
        max_reserved_mock.assert_not_called()

    def test_inactive_material_cannot_be_reserved(self):
        with self.assertRaises(HTTPException) as raised:
            _validate_materiel_actif(SimpleNamespace(nom="Talkie", statut=False))

        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("Materiel inactif", raised.exception.detail)

    def test_active_material_can_be_reserved(self):
        _validate_materiel_actif(SimpleNamespace(nom="Talkie", statut=True))
        _validate_materiel_actif(SimpleNamespace(nom="Talkie", statut=None))


if __name__ == "__main__":
    unittest.main()
