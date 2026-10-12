import unittest
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import JSON, MetaData, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from core.env_loader import load_local_env

load_local_env()

from crud.finance import get_finance_kpis
from crud import facture as factures
from api.depenses.routes import _validate_depense_relations
from fastapi import HTTPException
from database.base import Base
from database.models import Activite, DemandeTeamBuilding, Depense, Facture, Offre, Paiement, Proforma
from database.schemas import FactureCreate, FactureUpdate, PaiementCreate


class FinanceTests(unittest.TestCase):
    def setUp(self):
        # Disposable database only. No connection to the application's database.
        self.engine = create_engine("sqlite://")
        metadata = MetaData()
        for table in Base.metadata.tables.values():
            table.to_metadata(metadata)
        for table in metadata.tables.values():
            for column in table.columns:
                if isinstance(column.type, JSONB):
                    column.type = JSON()
                    column.server_default = None
        names = ("facture", "paiement", "proformas", "depense", "offre", "activite", "materiel", "demandes_team_building")
        metadata.create_all(self.engine, tables=[metadata.tables[name] for name in names])
        self.db = Session(self.engine)
        self.addCleanup(self.engine.dispose)
        self.addCleanup(self.db.close)

    def proforma(self, reference="PRO-1", fees=200, **kwargs):
        values = dict(reference=reference, pole="teambuilding", client="Client test",
                      objet="Séminaire", nombre_personnes=10, date_proforma=date(2026, 9, 1),
                      frais_agence=fees, total_ttc=1236, tva_frais_agence=36)
        values.update(kwargs)
        record = Proforma(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def facture(self, reference="FAC-1", proforma=None, **kwargs):
        values = dict(reference_interne=reference, pole="teambuilding", client="Client test",
                      montant_facture=1236, statut="non_payee", proforma_id=proforma.id if proforma else None)
        values.update(kwargs)
        record = Facture(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def expense(self, amount, **kwargs):
        values = dict(titre="Frais de mission", pole="teambuilding", montant=amount)
        values.update(kwargs)
        self.db.add(Depense(**values))
        self.db.flush()

    def report(self, pole=None):
        self.db.commit()
        self.db.expire_all()
        return get_finance_kpis(self.db, pole=pole)

    def test_real_revenue_is_fees_excluding_vat_and_profit_uses_fees(self):
        proforma = self.proforma()
        facture = self.facture(proforma=proforma)
        self.db.add_all([Paiement(facture_id=facture.id, montant=300), Paiement(facture_id=facture.id, montant=200)])
        self.expense(30, facture_id=facture.id)
        self.expense(50, proforma_id=proforma.id)

        report = self.report()
        total = report["total"]
        self.assertEqual(total["ca_global"], 1236)
        self.assertEqual(total["ca_reel"], 200)
        self.assertEqual(total["encaisse"], 500)
        self.assertEqual(total["reste_a_encaisser"], 736)
        self.assertEqual(total["depenses"], 80)
        self.assertEqual(total["benefice"], 120)
        self.assertEqual(total["taux_benefice"], 60)
        self.assertEqual(len(report["missions"]), 1)
        self.assertEqual(report["missions"][0]["benefice"], 120)

    def test_all_legacy_and_admin_links_resolve_to_one_mission_once(self):
        offre = Offre(demande_id=42, reference="OFF-42", titre="Mission client")
        self.db.add(offre)
        self.db.flush()
        activity = Activite(offre_id=offre.id, titre="Activité", site_id=1,
                            date_debut=datetime(2025, 1, 1), date_fin=datetime(2025, 1, 2))
        self.db.add(activity)
        self.db.flush()
        proforma = self.proforma(offre_id=offre.id)
        facture = self.facture(proforma=proforma)
        for link in (
            {"facture_id": facture.id}, {"proforma_id": proforma.id},
            {"demande_team_building_id": 42}, {"offre_id": offre.id},
            {"activite_id": activity.id, "offre_id": offre.id, "facture_id": facture.id},
        ):
            self.expense(10, **link)

        report = self.report()
        self.assertEqual(len(report["missions"]), 1)
        self.assertEqual(report["missions"][0]["id"], "teambuilding:demande_team_building_id:42")
        self.assertEqual(report["missions"][0]["depenses"], 50)
        self.assertEqual(report["missions"][0]["benefice"], 150)

    def test_same_client_different_requests_remain_separate(self):
        for number in (1, 2):
            proforma = self.proforma(f"PRO-{number}", demande_team_building_id=number)
            self.facture(f"FAC-{number}", proforma=proforma)
        self.expense(250, demande_team_building_id=2)
        report = self.report()
        self.assertEqual(len(report["missions"]), 2)
        self.assertEqual(sorted(row["benefice"] for row in report["missions"]), [-50, 200])
        self.assertEqual(report["total"]["benefice"], 150)

    def test_unassigned_expenses_reduce_total_without_arbitrary_allocation(self):
        self.facture(proforma=self.proforma())
        self.expense(50)
        report = self.report()
        self.assertEqual(report["total"]["depenses_non_affectees"], 50)
        self.assertEqual(report["total"]["benefice"], 150)
        self.assertEqual(report["missions"][0]["benefice"], 200)
        self.assertEqual(report["poles"]["teambuilding"]["depenses_non_affectees"], 50)

    def test_canceled_invoice_and_unbilled_proforma_do_not_generate_revenue(self):
        self.proforma("DRAFT", fees=9999)
        canceled = self.facture(proforma=self.proforma(), statut="annulee")
        self.expense(20, facture_id=canceled.id)
        report = self.report()
        self.assertEqual(report["total"]["ca_global"], 0)
        self.assertEqual(report["total"]["ca_reel"], 0)
        self.assertEqual(report["total"]["benefice"], -20)
        self.assertEqual(report["total"]["taux_benefice"], 0)
        self.assertEqual(report["missions"][0]["depenses"], 20)

    def test_fee_is_not_duplicated_by_multiple_invoices_or_payments(self):
        proforma = self.proforma()
        self.facture("FAC-A", proforma=proforma, montant_facture=600)
        self.facture("FAC-B", proforma=proforma, montant_facture=636)
        report = self.report()
        self.assertEqual(report["total"]["ca_global"], 1236)
        self.assertEqual(report["total"]["ca_reel"], 200)

    def test_missing_proforma_is_reported_and_not_treated_as_agency_revenue(self):
        self.facture(montant_facture=9999)
        self.facture("ZERO-FEES", proforma=self.proforma(fees=0))
        report = self.report()
        self.assertEqual(report["total"]["ca_reel"], 0)
        self.assertEqual(report["total"]["factures_sans_frais_agence"], 1)
        self.assertEqual(sum(row["factures_sans_frais_agence"] for row in report["missions"]), 1)

    def test_invoice_request_also_resolves_expenses_on_its_unlinked_proforma(self):
        proforma = self.proforma()
        self.facture(proforma=proforma, demande_team_building_id=42)
        self.expense(20, proforma_id=proforma.id)
        self.expense(30, demande_team_building_id=42)
        report = self.report()
        self.assertEqual(len(report["missions"]), 1)
        self.assertEqual(report["missions"][0]["depenses"], 50)

    def test_poles_and_tourism_request_types_are_isolated(self):
        self.facture("TB", proforma=self.proforma("TB", demande_team_building_id=1))
        for field in ("demande_tourisme_id", "demande_tourisme_custom_id"):
            proforma = self.proforma(field, fees=100, pole="tourisme", **{field: 1})
            self.facture(field, proforma=proforma, pole="tourisme")
            self.expense(40, pole="tourisme", **{field: 1})
        self.facture("PROD", pole="production", montant_facture=500)
        self.expense(25, pole="production")
        report = self.report()
        self.assertEqual(len(report["missions"]), 4)
        self.assertEqual(report["poles"]["tourisme"]["benefice"], 120)
        self.assertEqual(report["poles"]["production"]["benefice"], -25)
        self.assertEqual(report["total"]["ca_reel"], 400)
        filtered = self.report(pole="teambuilding")
        self.assertEqual(filtered["total"], report["poles"]["teambuilding"])
        self.assertEqual(len(filtered["missions"]), 1)

    def test_amounts_are_summed_as_decimals(self):
        self.facture("A", proforma=self.proforma("A", fees=Decimal("0.10")))
        self.facture("B", proforma=self.proforma("B", fees=Decimal("0.20")))
        self.expense(Decimal("0.10"))
        report = self.report()
        self.assertEqual(report["total"]["ca_reel"], 0.3)
        self.assertEqual(report["total"]["benefice"], 0.2)

    def test_empty_database_has_zero_totals(self):
        report = self.report()
        self.assertEqual(report["missions"], [])
        self.assertEqual(report["total"]["benefice"], 0)
        self.assertEqual(report["total"]["taux_benefice"], 0)

    def test_manual_invoice_fees_are_included_for_production(self):
        facture = factures.create_facture(self.db, FactureCreate(
            pole="production", client="Client production", montant_facture=1000, frais_agence=350,
        ))
        self.expense(100, pole="production", facture_id=facture.id)
        report = self.report()
        self.assertEqual(report["poles"]["production"]["ca_reel"], 350)
        self.assertEqual(report["poles"]["production"]["benefice"], 250)
        self.assertEqual(report["total"]["factures_sans_frais_agence"], 0)

    def test_expenses_before_invoicing_show_request_name_and_negative_result(self):
        self.db.add(DemandeTeamBuilding(
            id=42, entreprise="Entreprise ABC", nom_contact="Contact", telephone_contact="000",
            email_contact="test@example.com", nombre_participants=10, objectif="Cohésion d’équipe",
        ))
        self.expense(80, demande_team_building_id=42)
        mission = self.report()["missions"][0]
        self.assertEqual(mission["client"], "Entreprise ABC")
        self.assertEqual(mission["titre"], "Cohésion d’équipe")
        self.assertEqual(mission["benefice"], -80)

    def test_invoiced_fees_survive_later_proforma_edits(self):
        proforma = self.proforma()
        facture = factures.create_facture_from_proforma(self.db, proforma)
        self.assertEqual(facture.frais_agence, Decimal("200"))
        proforma.frais_agence = 800
        self.db.commit()
        factures.update_facture(self.db, facture, FactureUpdate(numero_fne="FNE-1"))
        report = self.report()
        self.assertEqual(report["total"]["ca_reel"], 200)

    def test_generic_create_copies_fees_and_rejects_duplicate_active_proforma(self):
        proforma = self.proforma()
        payload = FactureCreate(pole="teambuilding", client="Client test", montant_facture=1236, proforma_id=proforma.id)
        facture = factures.create_facture(self.db, payload)
        self.assertEqual(facture.frais_agence, Decimal("200"))
        with self.assertRaisesRegex(ValueError, "active existe"):
            factures.create_facture(self.db, payload)

    def test_linking_a_proforma_or_entering_manual_fees_updates_real_revenue(self):
        facture = self.facture()
        self.db.commit()
        factures.update_facture(self.db, facture, FactureUpdate(frais_agence=125))
        self.assertEqual(self.report()["total"]["ca_reel"], 125)
        proforma = self.proforma()
        factures.update_facture(self.db, facture, FactureUpdate(proforma_id=proforma.id))
        self.assertEqual(self.report()["total"]["ca_reel"], 200)
        factures.update_facture(self.db, facture, FactureUpdate(frais_agence=0))
        self.assertEqual(self.report()["total"]["ca_reel"], 0)
        self.assertEqual(self.report()["total"]["factures_sans_frais_agence"], 0)

    def test_fee_cannot_exceed_invoice_amount(self):
        with self.assertRaisesRegex(ValueError, "frais d'agence"):
            factures.create_facture(self.db, FactureCreate(
                pole="production", client="Client test", montant_facture=100, frais_agence=101,
            ))

    def test_legacy_duplicate_with_one_snapshot_does_not_add_proforma_fees_again(self):
        proforma = self.proforma()
        self.facture("A", proforma=proforma, frais_agence=180)
        self.facture("B", proforma=proforma)
        self.assertEqual(self.report()["total"]["ca_reel"], 180)

    def test_invoice_comparison_tracks_purchases_gains_and_pending_items(self):
        proforma = self.proforma(
            fees=10,
            sections=[{
                "nom": "Séjour",
                "prestations": [
                    {"designation": "Hôtel", "quantite": 1, "prix_unitaire": 50, "montant_ht": 50},
                    {"designation": "Transport", "quantite": 1, "prix_unitaire": 30, "montant_ht": 30},
                ],
            }],
            sous_total_ht=80,
            total_ttc=92,
            tva_frais_agence=2,
        )
        facture = factures.create_facture_from_proforma(self.db, proforma)
        self.expense(40, facture_id=facture.id, facture_ligne_cle="section-1-ligne-1")
        self.expense(5, facture_id=facture.id)
        self.db.commit()

        comparison = factures.get_facture_comparatif(self.db, facture)
        hotel, transport = comparison["lignes"]
        self.assertEqual(hotel["statut"], "gain")
        self.assertEqual(hotel["ecart"], 10)
        self.assertEqual(transport["statut"], "non_achete")
        self.assertIsNone(transport["ecart"])
        self.assertEqual(comparison["resume"]["gain_achats_constate"], 10)
        self.assertEqual(comparison["resume"]["achats_restants_factures"], 30)
        self.assertEqual(comparison["resume"]["resultat_constate"], 15)
        self.assertEqual(comparison["resume"]["ecart_facture_proforma"], 0)
        self.assertEqual(comparison["result_status"], "provisoire")
        report = self.report()
        self.assertEqual(report["total"]["gain_achats"], 10)
        self.assertEqual(report["total"]["depenses_hors_postes"], 5)
        self.assertEqual(report["total"]["benefice"], 15)

        factures.create_paiement(self.db, facture, PaiementCreate(montant=92))
        self.expense(30, facture_id=facture.id, facture_ligne_cle="section-1-ligne-2")
        self.db.commit()
        comparison = factures.get_facture_comparatif(self.db, facture)
        self.assertEqual(comparison["result_status"], "realise")
        self.assertEqual(comparison["resume"]["postes_non_achetes"], 0)
        self.assertEqual(comparison["resume"]["resultat_constate"], 15)
        self.assertEqual(self.report()["total"]["benefice"], 15)

    def test_invoice_comparison_uses_frozen_proforma_snapshot(self):
        proforma = self.proforma(
            sections=[{
                "nom": "Hébergement",
                "prestations": [{"designation": "Hôtel", "montant_ht": 50}],
            }],
            sous_total_ht=50,
        )
        facture = factures.create_facture_from_proforma(self.db, proforma)
        proforma.sections = [{
            "nom": "Hébergement",
            "prestations": [{"designation": "Hôtel modifié", "montant_ht": 500}],
        }]
        self.db.commit()

        comparison = factures.get_facture_comparatif(self.db, facture)
        self.assertEqual(comparison["lignes"][0]["designation"], "Hôtel")
        self.assertEqual(comparison["lignes"][0]["montant_facture"], 50)
        facture.montant_facture = 1300
        self.db.commit()
        comparison = factures.get_facture_comparatif(self.db, facture)
        self.assertEqual(comparison["resume"]["ecart_facture_proforma"], 64)

    def test_manual_invoice_without_breakdown_is_marked_non_comparable(self):
        facture = factures.create_facture(self.db, FactureCreate(
            pole="production", client="Client production", montant_facture=500, frais_agence=100,
        ))
        comparison = factures.get_facture_comparatif(self.db, facture)
        self.assertFalse(comparison["has_breakdown"])
        self.assertEqual(comparison["result_status"], "non_comparable")

    def test_expense_invoice_line_must_exist_on_invoice(self):
        proforma = self.proforma(
            sections=[{
                "nom": "Séjour",
                "prestations": [{"designation": "Hôtel", "montant_ht": 50}],
            }],
            sous_total_ht=50,
        )
        facture = factures.create_facture_from_proforma(self.db, proforma)
        valid = {
            "pole": "teambuilding",
            "facture_id": facture.id,
            "facture_ligne_cle": "section-1-ligne-1",
        }
        _validate_depense_relations(self.db, valid)
        with self.assertRaises(HTTPException):
            _validate_depense_relations(self.db, {**valid, "facture_ligne_cle": "inconnue"})
        with self.assertRaises(HTTPException):
            _validate_depense_relations(self.db, {
                "pole": "teambuilding",
                "facture_ligne_cle": "section-1-ligne-1",
            })

    def test_request_expense_is_not_counted_twice_when_request_has_two_invoices(self):
        first = self.proforma("P1", demande_team_building_id=42)
        second = self.proforma("P2", demande_team_building_id=42)
        first_invoice = factures.create_facture_from_proforma(self.db, first)
        factures.create_facture_from_proforma(self.db, second)
        self.expense(75, demande_team_building_id=42)
        self.db.commit()

        comparison = factures.get_facture_comparatif(self.db, first_invoice)
        self.assertEqual(comparison["resume"]["achats_enregistres"], 0)
        self.assertEqual(comparison["resume"]["depenses_a_affecter"], 75)
        self.assertEqual(len(comparison["depenses_a_affecter"]), 1)

    def test_team_dashboard_matches_finance_and_hides_financials_when_requested(self):
        from crud.dashboard_teambuilding import get_dashboard
        self.facture(proforma=self.proforma())
        self.expense(50)
        report = self.report()
        dashboard = get_dashboard(self.db)
        self.assertEqual(dashboard["stats"]["chiffre_affaires_reel"], 200)
        self.assertEqual(dashboard["stats"]["marge_estimee"], 150)
        self.assertEqual(dashboard["finance"]["total"], report["poles"]["teambuilding"])
        hidden = get_dashboard(self.db, include_financials=False)
        self.assertIsNone(hidden["finance"])
        self.assertNotIn("marge_estimee", hidden["stats"])
        self.assertNotIn("chiffre_affaires_reel", hidden["stats"])

    def test_team_dashboard_route_respects_financial_role(self):
        from api.dashboard_teambuilding.routes import get_dashboard_teambuilding
        for role, expected in (("admin", True), ("super_admin", True), ("utilisateur", False), ("superviseur_teambuilding", False)):
            with self.subTest(role=role), patch("api.dashboard_teambuilding.routes.crud_dashboard.get_dashboard") as dashboard:
                get_dashboard_teambuilding(db=self.db, current_user=SimpleNamespace(role=role))
                dashboard.assert_called_once_with(self.db, include_financials=expected)


if __name__ == "__main__":
    unittest.main()
