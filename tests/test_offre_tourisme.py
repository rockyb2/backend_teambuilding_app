import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from api.demandes_tourisme import routes as demande_tourisme_routes
from api.offres_tourisme import routes as offre_tourisme_routes
from crud import offre_tourisme as crud_offre_tourisme
from database.schemas import DemandeTourismeStatutUpdate


class OffreTourismeTests(unittest.TestCase):
    def build_sync_db(self, demande, offer_statuses):
        db = Mock()
        demande_query = Mock()
        status_query = Mock()
        db.query.side_effect = [demande_query, status_query]
        demande_query.filter.return_value.first.return_value = demande
        status_query.filter.return_value.all.return_value = [
            (status,) for status in offer_statuses
        ]
        return db

    def test_reference_is_generated_by_month(self):
        db = Mock()
        db.get_bind.return_value = None
        db.query.return_value.filter.return_value.all.return_value = [
            ("OFF-TOUR-202606-001",),
            ("OFF-TOUR-202606-004",),
        ]

        reference = crud_offre_tourisme.generate_offre_tourisme_reference(
            db,
            datetime(2026, 6, 15),
        )

        self.assertEqual(reference, "OFF-TOUR-202606-005")

    def test_sent_offer_moves_circuit_request_to_quote_sent(self):
        demande = SimpleNamespace(
            id=12,
            statut="contactee",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_sync_db(demande, ["envoyee"])

        crud_offre_tourisme._sync_demande_status_from_offres(
            db,
            demande_tourisme_id=demande.id,
            utilisateur_id=7,
        )

        self.assertEqual(demande.statut, "devis_envoye")
        self.assertEqual(demande.statut_modifie_par_id, 7)
        db.add.assert_called_once()

    def test_validated_offer_moves_request_to_validated(self):
        demande = SimpleNamespace(
            id=12,
            statut="devis_envoye",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_sync_db(demande, ["envoyee", "validee"])

        crud_offre_tourisme._sync_demande_status_from_offres(
            db,
            demande_tourisme_id=demande.id,
            utilisateur_id=7,
        )

        self.assertEqual(demande.statut, "validee")

    def test_refused_offer_moves_request_to_refused(self):
        demande = SimpleNamespace(
            id=12,
            statut="devis_envoye",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_sync_db(demande, ["refusee"])

        crud_offre_tourisme._sync_demande_status_from_offres(
            db,
            demande_tourisme_id=demande.id,
            utilisateur_id=7,
        )

        self.assertEqual(demande.statut, "refusee")

    def test_offer_does_not_reopen_cancelled_request(self):
        demande = SimpleNamespace(
            id=12,
            statut="annulee",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = Mock()
        demande_query = Mock()
        db.query.return_value = demande_query
        demande_query.filter.return_value.first.return_value = demande

        crud_offre_tourisme._sync_demande_status_from_offres(
            db,
            demande_tourisme_id=demande.id,
            utilisateur_id=7,
        )

        self.assertEqual(demande.statut, "annulee")
        self.assertEqual(db.query.call_count, 1)

    def test_offer_requires_exactly_one_request(self):
        with self.assertRaises(HTTPException) as raised:
            offre_tourisme_routes._validate_target(Mock(), 1, 2)

        self.assertEqual(raised.exception.status_code, 422)

    def test_manual_request_status_only_allows_new_to_contacted(self):
        db = Mock()
        demande = SimpleNamespace(id=12, statut="contactee")
        with patch.object(
            demande_tourisme_routes.crud_demande_tourisme,
            "get_demande_tourisme",
            return_value=demande,
        ):
            with self.assertRaises(HTTPException) as raised:
                demande_tourisme_routes.update_demande_tourisme_statut(
                    demande.id,
                    DemandeTourismeStatutUpdate(statut="validee"),
                    db,
                    SimpleNamespace(id_utilisateur=7),
                )

        self.assertEqual(raised.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
