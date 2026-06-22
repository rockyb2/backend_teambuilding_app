import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.env_loader import load_local_env

load_local_env()

from fastapi import HTTPException
from pydantic import ValidationError

from api.demandes_team_building import routes as demande_team_building_routes
from crud import utilisateur as crud_utilisateur
from crud import demande_team_building as crud_demande_team_building
from crud import offre as crud_offre
from database.schemas import (
    DemandeTeamBuildingCreate,
    DemandeTeamBuildingStatutUpdate,
    OffreCreate,
    UtilisateurProfileUpdate,
)


class UtilisateurProfileTests(unittest.TestCase):
    def test_profile_contract_rejects_administrative_fields(self):
        with self.assertRaises(ValidationError):
            UtilisateurProfileUpdate(nom="Test", role="super_admin")

    def test_profile_update_only_changes_personal_fields(self):
        db = Mock()
        utilisateur = SimpleNamespace(
            nom="Ancien",
            prenom=None,
            email="ancien@example.com",
            image_utilisateur=None,
        )
        payload = UtilisateurProfileUpdate(
            nom="Nouveau",
            prenom="Prenom",
            email="nouveau@example.com",
            image_utilisateur="https://example.com/avatar.jpg",
        )

        result = crud_utilisateur.update_utilisateur_profile(db, utilisateur, payload)

        self.assertIs(result, utilisateur)
        self.assertEqual(utilisateur.nom, "Nouveau")
        self.assertEqual(utilisateur.email, "nouveau@example.com")
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(utilisateur)

    def test_password_change_requires_current_password(self):
        db = Mock()
        utilisateur = SimpleNamespace(mot_de_passe="hash-actuel")

        with patch.object(crud_utilisateur, "verify_password", return_value=False):
            changed = crud_utilisateur.change_utilisateur_password(
                db,
                utilisateur,
                "incorrect",
                "nouveau-secret",
            )

        self.assertFalse(changed)
        self.assertEqual(utilisateur.mot_de_passe, "hash-actuel")
        db.commit.assert_not_called()

    def test_password_change_hashes_and_saves_new_password(self):
        db = Mock()
        utilisateur = SimpleNamespace(mot_de_passe="hash-actuel")

        with (
            patch.object(crud_utilisateur, "verify_password", return_value=True),
            patch.object(crud_utilisateur, "get_password_hash", return_value="nouveau-hash"),
        ):
            changed = crud_utilisateur.change_utilisateur_password(
                db,
                utilisateur,
                "actuel",
                "nouveau-secret",
            )

        self.assertTrue(changed)
        self.assertEqual(utilisateur.mot_de_passe, "nouveau-hash")
        db.commit.assert_called_once_with()

    def test_get_utilisateur_uses_write_session(self):
        db = Mock()
        persistent_user = SimpleNamespace(id_utilisateur=7, mot_de_passe="hash")
        query = db.query.return_value
        query.filter.return_value.first.return_value = persistent_user

        result = crud_utilisateur.get_utilisateur(db, 7)

        self.assertIs(result, persistent_user)
        db.query.assert_called_once()
        query.filter.assert_called_once()

    def test_record_login_updates_timestamp(self):
        db = Mock()
        utilisateur = SimpleNamespace(derniere_connexion=None)

        result = crud_utilisateur.record_login(db, utilisateur)

        self.assertIs(result, utilisateur)
        self.assertIsNotNone(utilisateur.derniere_connexion)
        self.assertIsNotNone(utilisateur.derniere_connexion.tzinfo)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(utilisateur)

    def test_team_building_status_update_tracks_user(self):
        db = Mock()
        demande = SimpleNamespace(
            id=12,
            statut="nouvelle",
            statut_modifie_le=None,
            statut_modifie_par_id=None,
        )

        with patch.object(
            crud_demande_team_building,
            "get_demande_team_building",
            return_value=demande,
        ):
            result = crud_demande_team_building.update_demande_team_building_statut(
                db,
                demande,
                "contactee",
                7,
            )

        self.assertIs(result, demande)
        self.assertEqual(demande.statut, "contactee")
        self.assertEqual(demande.statut_modifie_par_id, 7)
        self.assertIsNotNone(demande.statut_modifie_le)
        db.commit.assert_called_once_with()

    def test_team_building_status_contract_uses_stable_technical_values(self):
        payload = DemandeTeamBuildingStatutUpdate(statut="confirmee")
        self.assertEqual(payload.statut, "confirmee")

        with self.assertRaises(ValidationError):
            DemandeTeamBuildingStatutUpdate(statut="confirmée")

    def test_team_building_manual_status_only_allows_new_to_contacted(self):
        db = Mock()
        demande = SimpleNamespace(id=12, statut="contactee")

        with patch.object(
            demande_team_building_routes.crud_demande_team_building,
            "get_demande_team_building",
            return_value=demande,
        ):
            with self.assertRaises(HTTPException) as raised:
                demande_team_building_routes.update_demande_team_building_statut(
                    demande.id,
                    DemandeTeamBuildingStatutUpdate(statut="confirmee"),
                    db,
                    SimpleNamespace(id_utilisateur=7),
                )

        self.assertEqual(raised.exception.status_code, 409)

    def test_team_building_manual_status_allows_new_to_contacted(self):
        db = Mock()
        demande = SimpleNamespace(id=12, statut="nouvelle")

        with (
            patch.object(
                demande_team_building_routes.crud_demande_team_building,
                "get_demande_team_building",
                return_value=demande,
            ),
            patch.object(
                demande_team_building_routes.crud_demande_team_building,
                "update_demande_team_building_statut",
                return_value=demande,
            ) as update_status,
        ):
            demande_team_building_routes.update_demande_team_building_statut(
                demande.id,
                DemandeTeamBuildingStatutUpdate(statut="contactee"),
                db,
                SimpleNamespace(id_utilisateur=7),
            )

        update_status.assert_called_once_with(db, demande, "contactee", 7)

    def test_team_building_full_update_preserves_current_status(self):
        db = Mock()
        demande = SimpleNamespace(id=12, statut="contactee")
        payload = DemandeTeamBuildingCreate(
            entreprise="Entreprise Test",
            nom_contact="Contact Test",
            telephone_contact="0102030405",
            email_contact="contact@example.com",
            nombre_participants=10,
            objectif="Cohesion",
            statut="confirmee",
        )

        with (
            patch.object(
                demande_team_building_routes.crud_demande_team_building,
                "get_demande_team_building",
                return_value=demande,
            ),
            patch.object(
                demande_team_building_routes.crud_demande_team_building,
                "update_demande_team_building",
                return_value=demande,
            ) as update_demande,
        ):
            demande_team_building_routes.update_demande_team_building(
                demande.id,
                payload,
                db,
                SimpleNamespace(id_utilisateur=7),
            )

        updates = update_demande.call_args.args[2]
        self.assertEqual(updates["statut"], "contactee")

    def test_internal_team_building_creation_forces_source_and_creator(self):
        db = Mock()
        db.refresh.side_effect = lambda item: setattr(item, "id", 42)
        payload = DemandeTeamBuildingCreate(
            entreprise="Entreprise Test",
            nom_contact="Contact Test",
            telephone_contact="0102030405",
            email_contact="contact@example.com",
            nombre_participants=10,
            objectif="Cohesion",
            source="site_web",
        )

        with patch.object(
            crud_demande_team_building,
            "get_demande_team_building",
            side_effect=lambda _, demande_id: SimpleNamespace(
                id=demande_id,
                source="crm",
                created_by_id=7,
            ),
        ):
            result = crud_demande_team_building.create_demande_team_building(
                db,
                payload,
                source="crm",
                created_by_id=7,
            )

        created = db.add.call_args.args[0]
        self.assertEqual(created.source, "crm")
        self.assertEqual(created.created_by_id, 7)
        self.assertEqual(result.created_by_id, 7)

    def test_offer_creation_forces_current_user_as_creator(self):
        db = Mock()
        payload = OffreCreate(
            demande_id=1,
            titre="Offre Test",
            montant_total=150000,
            id_utilisateur_cr=99,
        )

        with (
            patch.object(crud_offre, "generate_offre_reference", return_value="OFF-TEST-001"),
            patch.object(crud_offre, "_sync_demande_status_from_offres"),
        ):
            result = crud_offre.create_offre(db, payload, created_by_id=7)

        self.assertEqual(result.id_utilisateur_cr, 7)
        self.assertEqual(result.reference, "OFF-TEST-001")


if __name__ == "__main__":
    unittest.main()
