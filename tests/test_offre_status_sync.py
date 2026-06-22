import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from core.env_loader import load_local_env

load_local_env()

from crud import offre as crud_offre


class OffreStatusSyncTests(unittest.TestCase):
    def build_db(self, demande, offer_statuses):
        db = Mock()
        demande_query = Mock()
        status_query = Mock()
        db.query.side_effect = [demande_query, status_query]
        demande_query.filter.return_value.first.return_value = demande
        status_query.filter.return_value.all.return_value = [(status,) for status in offer_statuses]
        return db

    def test_sent_offer_moves_request_to_quote_sent(self):
        demande = SimpleNamespace(
            statut="contactee",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_db(demande, ["envoyee"])

        crud_offre._sync_demande_status_from_offres(db, 12, utilisateur_id=7)

        self.assertEqual(demande.statut, "devis_envoye")
        self.assertEqual(demande.statut_modifie_par_id, 7)
        self.assertIsNotNone(demande.statut_modifie_le)

    def test_validated_offer_moves_request_to_confirmed(self):
        demande = SimpleNamespace(
            statut="devis_envoye",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_db(demande, ["envoyee", "validee"])

        crud_offre._sync_demande_status_from_offres(db, 12, utilisateur_id=7)

        self.assertEqual(demande.statut, "confirmee")

    def test_sent_offer_does_not_downgrade_confirmed_request(self):
        demande = SimpleNamespace(
            statut="confirmee",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_db(demande, ["envoyee"])

        crud_offre._sync_demande_status_from_offres(db, 12, utilisateur_id=7)

        self.assertEqual(demande.statut, "confirmee")

    def test_offer_does_not_reopen_cancelled_request(self):
        demande = SimpleNamespace(
            statut="annulee",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_db(demande, ["validee"])

        crud_offre._sync_demande_status_from_offres(db, 12, utilisateur_id=7)

        self.assertEqual(demande.statut, "annulee")
        self.assertEqual(db.query.call_count, 1)

    def test_all_terminal_offers_move_request_to_cancelled(self):
        demande = SimpleNamespace(
            statut="devis_envoye",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_db(demande, ["annulee", "refusee", "expiree"])

        crud_offre._sync_demande_status_from_offres(db, 12, utilisateur_id=7)

        self.assertEqual(demande.statut, "annulee")
        self.assertEqual(demande.statut_modifie_par_id, 7)
        self.assertIsNotNone(demande.statut_modifie_le)

    def test_terminal_offer_does_not_override_sent_offer(self):
        demande = SimpleNamespace(
            statut="contactee",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_db(demande, ["annulee", "envoyee"])

        crud_offre._sync_demande_status_from_offres(db, 12, utilisateur_id=7)

        self.assertEqual(demande.statut, "devis_envoye")

    def test_terminal_offers_do_not_cancel_confirmed_request(self):
        demande = SimpleNamespace(
            statut="confirmee",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )
        db = self.build_db(demande, ["annulee"])

        crud_offre._sync_demande_status_from_offres(db, 12, utilisateur_id=7)

        self.assertEqual(demande.statut, "confirmee")


if __name__ == "__main__":
    unittest.main()
