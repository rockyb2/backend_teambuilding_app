import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from core.env_loader import load_local_env

load_local_env()

from api.activites.routes import _validate_activite_relations, _validate_offre_available


class ActiviteOffreRulesTests(unittest.TestCase):
    @patch("api.activites.routes.crud_offre.get_offre")
    def test_activity_can_use_validated_offer(self, get_offre_mock):
        get_offre_mock.return_value = SimpleNamespace(statut="validee")

        _validate_activite_relations(Mock(), {"offre_id": 12})

    @patch("api.activites.routes.crud_offre.get_offre")
    def test_activity_cannot_use_cancelled_offer(self, get_offre_mock):
        get_offre_mock.return_value = SimpleNamespace(statut="annulee")

        with self.assertRaises(HTTPException) as raised:
            _validate_activite_relations(Mock(), {"offre_id": 12})

        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("offre validee", raised.exception.detail)

    @patch("api.activites.routes.crud_activite.get_activite_by_offre")
    def test_offer_cannot_be_reused_by_another_activity(self, get_activite_by_offre_mock):
        get_activite_by_offre_mock.return_value = SimpleNamespace(
            id=5,
            reference="ACT-202606-001",
            titre="Seminaire",
        )

        with self.assertRaises(HTTPException) as raised:
            _validate_offre_available(Mock(), offre_id=12, exclude_activite_id=6)

        self.assertEqual(raised.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
