from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, load_only

from crud.facture import get_facture_lines
from database.models import (
    Activite, DemandeTeamBuilding, DemandeTourisme, DemandeTourismeCustom,
    Depense, Facture, Offre, Paiement, Proforma,
)


POLES = ("teambuilding", "tourisme", "production")
ACTIVE_FACTURE_STATUSES = ("non_payee", "partiellement_payee", "payee")
REQUEST_FIELDS = (
    ("teambuilding", "demande_team_building_id"),
    ("tourisme", "demande_tourisme_id"),
    ("tourisme", "demande_tourisme_custom_id"),
)


def _decimal(value) -> Decimal:
    return Decimal(str(value or 0))


def _empty_amounts() -> dict:
    return dict.fromkeys((
        "ca_global", "ca_reel", "encaisse", "depenses",
        "gain_achats", "depenses_hors_postes", "prestations_achetees_facturees",
    ), Decimal("0"))


def _bucket(amounts: dict) -> dict:
    ca_global, ca_reel = amounts["ca_global"], amounts["ca_reel"]
    benefice = ca_reel + amounts["gain_achats"] - amounts["depenses_hors_postes"]
    base_marge = ca_reel + amounts["prestations_achetees_facturees"]
    return {
        **{key: float(value) for key, value in amounts.items()},
        "ca": float(ca_global),  # Compatibility with existing API consumers.
        "reste_a_encaisser": float(max(ca_global - amounts["encaisse"], 0)),
        "benefice": float(benefice),
        "taux_benefice": float(round(benefice / base_marge * 100, 1)) if base_marge else 0.0,
    }


class _MissionResolver:
    """Group a customer's request and its documents into a single mission.

    Without a request, retain the offer, activity, proforma or invoice identity.
    Never match missions by client name, and never split an expense over links.
    """

    def __init__(self, factures, proformas, offres, activites):
        self.factures = factures
        self.proformas = proformas
        self.offres = offres
        self.activites = activites
        self.proforma_requests = {}
        for facture in factures.values():
            request = self.request(facture)
            proforma = proformas.get(facture.proforma_id)
            if proforma and proforma.pole == facture.pole and request:
                self.proforma_requests.setdefault(facture.proforma_id, set()).add(request)

    def request(self, record):
        for pole, field in REQUEST_FIELDS:
            request_id = getattr(record, field, None)
            if request_id and record.pole == pole:
                return (pole, field, request_id)
        return None

    def offre(self, record):
        if record.demande_id:
            return ("teambuilding", "demande_team_building_id", record.demande_id)
        return ("teambuilding", "offre", record.id)

    def activite(self, record):
        if record.demande_id:
            return ("teambuilding", "demande_team_building_id", record.demande_id)
        if record.offre_id in self.offres:
            return self.offre(self.offres[record.offre_id])
        return ("teambuilding", "activite", record.id)

    def proforma(self, record):
        request = self.request(record)
        if request:
            return request
        if record.pole == "teambuilding" and record.offre_id in self.offres:
            return self.offre(self.offres[record.offre_id])
        requests = self.proforma_requests.get(record.id, set())
        if len(requests) == 1:
            return next(iter(requests))
        return (record.pole, "proforma", record.id)

    def facture(self, record):
        proforma = self.proformas.get(record.proforma_id)
        if proforma and proforma.pole == record.pole:
            return self.proforma(proforma)
        return self.request(record) or (record.pole, "facture", record.id)

    def depense(self, record):
        # Legacy expenses can have several links: count the amount only once.
        for field, records, resolve in (
            ("facture_id", self.factures, self.facture),
            ("proforma_id", self.proformas, self.proforma),
            ("activite_id", self.activites, self.activite),
            ("offre_id", self.offres, self.offre),
        ):
            linked = records.get(getattr(record, field))
            if linked is not None:
                key = resolve(linked)
                if key[0] == record.pole:
                    return key
        return self.request(record)


def get_finance_kpis(db: Session, pole: str | None = None) -> dict:
    # Avoid loading document JSON or querying relationships for every mission.
    def indexed(model, fields):
        query = db.query(model).options(load_only(*fields))
        if pole and hasattr(model, "pole"):
            query = query.filter(model.pole == pole)
        return {item.id: item for item in query.all()}

    factures = indexed(Facture, (
        Facture.pole, Facture.statut, Facture.proforma_id, Facture.montant_facture, Facture.frais_agence,
        Facture.reference_interne, Facture.client, Facture.objet, Facture.proforma_snapshot,
        *(getattr(Facture, field) for _, field in REQUEST_FIELDS),
    ))
    proformas = indexed(Proforma, (
        Proforma.pole, Proforma.offre_id, Proforma.reference, Proforma.client,
        Proforma.objet, Proforma.frais_agence,
        *(getattr(Proforma, field) for _, field in REQUEST_FIELDS),
    ))
    offres = indexed(Offre, (Offre.demande_id, Offre.reference, Offre.titre)) if pole in (None, "teambuilding") else {}
    activites = indexed(Activite, (
        Activite.demande_id, Activite.offre_id, Activite.reference, Activite.titre,
    )) if pole in (None, "teambuilding") else {}
    resolver = _MissionResolver(factures, proformas, offres, activites)

    payment_query = (
        db.query(Paiement.facture_id, func.sum(Paiement.montant))
        .join(Facture, Facture.id == Paiement.facture_id)
        .filter(Facture.statut.in_(ACTIVE_FACTURE_STATUSES))
    )
    if pole:
        payment_query = payment_query.filter(Facture.pole == pole)
    payments = dict(payment_query.group_by(Paiement.facture_id).all())
    expense_query = db.query(Depense).options(load_only(
        Depense.pole, Depense.montant, Depense.facture_id, Depense.proforma_id,
        Depense.offre_id, Depense.activite_id, Depense.facture_ligne_cle,
        *(getattr(Depense, field) for _, field in REQUEST_FIELDS),
    ))
    if pole:
        expense_query = expense_query.filter(Depense.pole == pole)

    labels = {}
    for record in proformas.values():
        labels.setdefault(resolver.proforma(record), (record.reference, record.objet, record.client))
    for record in offres.values():
        key = resolver.offre(record)
        labels[key] = (record.reference, record.titre, labels.get(key, (None, None, ""))[2])
    for record in activites.values():
        key = resolver.activite(record)
        labels.setdefault(key, (record.reference, record.titre, ""))

    missions = {}
    selected_poles = (pole,) if pole else POLES
    unassigned = {key: Decimal("0") for key in selected_poles}
    counted_proformas = set()
    snapshotted_proformas = {
        facture.proforma_id for facture in factures.values()
        if facture.statut in ACTIVE_FACTURE_STATUSES and facture.frais_agence is not None
    }

    def mission(key, facture=None):
        if key not in missions:
            reference, titre, client = labels.get(key, (None, None, ""))
            missions[key] = {
                "id": ":".join(map(str, key)),
                "pole": key[0],
                "reference": reference or (facture.reference_interne if facture else f"Mission #{key[2]}"),
                "titre": titre or (facture.objet if facture else None) or "Mission",
                "client": client or (facture.client if facture else ""),
                "factures_sans_frais_agence": 0,
                **_empty_amounts(),
            }
        return missions[key]

    for facture in factures.values():
        if facture.statut not in ACTIVE_FACTURE_STATUSES:
            continue
        row = mission(resolver.facture(facture), facture)
        row["ca_global"] += _decimal(facture.montant_facture)
        row["encaisse"] += _decimal(payments.get(facture.id))
        proforma = proformas.get(facture.proforma_id)
        if facture.frais_agence is not None:
            row["ca_reel"] += _decimal(facture.frais_agence)
        elif proforma is None or proforma.pole != facture.pole:
            row["factures_sans_frais_agence"] += 1
        elif proforma.id not in counted_proformas and proforma.id not in snapshotted_proformas:
            # frais_agence stores the computed monetary amount, excluding VAT.
            row["ca_reel"] += _decimal(proforma.frais_agence)
            counted_proformas.add(proforma.id)

    facture_lines = {
        facture.id: {line["cle"]: _decimal(line["montant_ht"]) for line in get_facture_lines(facture)}
        for facture in factures.values()
        if facture.statut in ACTIVE_FACTURE_STATUSES
    }
    line_expenses = {}
    for expense in expense_query.all():
        key = resolver.depense(expense)
        if key:
            row = mission(key)
            amount = _decimal(expense.montant)
            row["depenses"] += amount
            line_key = (expense.facture_id, expense.facture_ligne_cle)
            if (
                expense.facture_ligne_cle
                and expense.facture_id in facture_lines
                and expense.facture_ligne_cle in facture_lines[expense.facture_id]
            ):
                line_expenses[line_key] = line_expenses.get(line_key, Decimal("0")) + amount
            else:
                row["depenses_hors_postes"] += amount
        else:
            unassigned[expense.pole] += _decimal(expense.montant)

    # A purchase gain only exists once at least one real expense has been
    # recorded for the invoiced line. Pending purchases do not create profit.
    for (facture_id, line_key), amount in line_expenses.items():
        facture = factures[facture_id]
        row = mission(resolver.facture(facture), facture)
        invoiced = facture_lines[facture_id][line_key]
        row["prestations_achetees_facturees"] += invoiced
        row["gain_achats"] += invoiced - amount

    # Expenses may precede invoices. Give those missions their request's name
    # without loading full request objects or issuing one query per expense.
    request_labels = (
        ("demande_team_building_id", DemandeTeamBuilding, DemandeTeamBuilding.objectif,
         (DemandeTeamBuilding.entreprise,)),
        ("demande_tourisme_id", DemandeTourisme, DemandeTourisme.titre_circuit,
         (DemandeTourisme.prenom, DemandeTourisme.nom)),
        ("demande_tourisme_custom_id", DemandeTourismeCustom, DemandeTourismeCustom.lieu_souhaite,
         (DemandeTourismeCustom.prenoms_client, DemandeTourismeCustom.nom_client)),
    )
    for kind, model, title_column, client_columns in request_labels:
        missing_labels = {
            key[2]: row for key, row in missions.items()
            if key[1] == kind and (not row["client"] or row["titre"] == "Mission")
        }
        if not missing_labels:
            continue
        for request in db.query(model.id, title_column, *client_columns).filter(model.id.in_(missing_labels)).all():
            row = missing_labels[request[0]]
            row["client"] = row["client"] or " ".join(value for value in request[2:] if value)
            if row["titre"] == "Mission":
                row["titre"] = request[1] or "Mission"

    poles = {}
    for selected_pole in selected_poles:
        amounts = _empty_amounts()
        missing = 0
        for row in missions.values():
            if row["pole"] == selected_pole:
                for field in amounts:
                    amounts[field] += row[field]
                missing += row["factures_sans_frais_agence"]
        amounts["depenses"] += unassigned[selected_pole]
        amounts["depenses_hors_postes"] += unassigned[selected_pole]
        poles[selected_pole] = {
            **_bucket(amounts),
            "depenses_non_affectees": float(unassigned[selected_pole]),
            "factures_sans_frais_agence": missing,
        }

    total_amounts = _empty_amounts()
    for row in missions.values():
        for field in total_amounts:
            total_amounts[field] += row[field]
    total_amounts["depenses"] += sum(unassigned.values())
    total_amounts["depenses_hors_postes"] += sum(unassigned.values())
    return {
        "total": {
            **_bucket(total_amounts),
            "depenses_non_affectees": float(sum(unassigned.values())),
            "factures_sans_frais_agence": sum(row["factures_sans_frais_agence"] for row in missions.values()),
        },
        "poles": poles,
        "missions": [
            {**row, **_bucket({field: row[field] for field in _empty_amounts()})}
            for row in sorted(missions.values(), key=lambda row: (row["pole"], row["reference"], row["id"]))
        ],
    }
