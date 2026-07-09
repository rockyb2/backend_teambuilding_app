from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import Depense, Facture, Paiement


POLES = ("teambuilding", "tourisme", "production")
ACTIVE_FACTURE_STATUSES = ("non_payee", "partiellement_payee", "payee")


def _money(value) -> float:
    return float(value or 0)


def _rate(benefice: float, ca: float) -> float:
    if not ca:
        return 0.0
    return round((benefice / ca) * 100, 1)


def _facture_query(db: Session):
    return db.query(Facture).filter(Facture.statut.in_(ACTIVE_FACTURE_STATUSES))


def _ca_by_pole(db: Session) -> dict[str, float]:
    rows = (
        _facture_query(db)
        .with_entities(Facture.pole, func.coalesce(func.sum(Facture.montant_facture), 0))
        .group_by(Facture.pole)
        .all()
    )
    return {pole: _money(total) for pole, total in rows}


def _encaisse_by_pole(db: Session) -> dict[str, float]:
    rows = (
        db.query(Facture.pole, func.coalesce(func.sum(Paiement.montant), 0))
        .join(Paiement, Paiement.facture_id == Facture.id)
        .filter(Facture.statut.in_(ACTIVE_FACTURE_STATUSES))
        .group_by(Facture.pole)
        .all()
    )
    return {pole: _money(total) for pole, total in rows}


def _depenses_by_pole(db: Session) -> dict[str, float]:
    rows = (
        db.query(Depense.pole, func.coalesce(func.sum(Depense.montant), 0))
        .group_by(Depense.pole)
        .all()
    )
    return {pole: _money(total) for pole, total in rows}


def _bucket(ca: float, encaisse: float, depenses: float) -> dict:
    reste = max(ca - encaisse, 0)
    benefice = ca - depenses
    return {
        "ca": ca,
        "encaisse": encaisse,
        "reste_a_encaisser": reste,
        "depenses": depenses,
        "benefice": benefice,
        "taux_benefice": _rate(benefice, ca),
    }


def get_finance_kpis(db: Session) -> dict:
    ca_map = _ca_by_pole(db)
    encaisse_map = _encaisse_by_pole(db)
    depenses_map = _depenses_by_pole(db)

    poles = {}
    for pole in POLES:
        poles[pole] = _bucket(
            ca=ca_map.get(pole, 0.0),
            encaisse=encaisse_map.get(pole, 0.0),
            depenses=depenses_map.get(pole, 0.0),
        )

    total_ca = sum(bucket["ca"] for bucket in poles.values())
    total_encaisse = sum(bucket["encaisse"] for bucket in poles.values())
    total_depenses = sum(bucket["depenses"] for bucket in poles.values())

    return {
        "total": _bucket(
            ca=total_ca,
            encaisse=total_encaisse,
            depenses=total_depenses,
        ),
        "poles": poles,
    }
