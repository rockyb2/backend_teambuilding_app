from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from database.models import (
    DemandeContact,
    DemandeTeamBuilding,
    DemandeTourisme,
    DemandeTourismeCustom,
    Materiel,
    NewsletterSubscriber,
    Offre,
    OffreTourisme,
    Proforma,
    Role,
    Utilisateur,
)


LOW_STOCK_THRESHOLD = 5
MONTH_LABELS = {
    1: "Jan.",
    2: "Fev.",
    3: "Mars",
    4: "Avr.",
    5: "Mai",
    6: "Juin",
    7: "Juil.",
    8: "Aout",
    9: "Sept.",
    10: "Oct.",
    11: "Nov.",
    12: "Dec.",
}
OFFER_STATUS_LABELS = {
    "brouillon": "Brouillons",
    "envoyee": "Envoyees",
    "validee": "Validees",
    "refusee": "Refusees",
    "expiree": "Expirees",
    "annulee": "Annulees",
}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _money(value) -> float:
    return float(value or 0)


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _shift_month(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    return date(month_index // 12, month_index % 12 + 1, 1)


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _as_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return datetime.min


def _last_six_months(today: date) -> list[dict]:
    current_month = _month_start(today)
    months = []
    for offset in range(-5, 1):
        month = _shift_month(current_month, offset)
        months.append(
            {
                "key": month.strftime("%Y-%m"),
                "label": MONTH_LABELS[month.month],
                "start": month,
                "end": _shift_month(month, 1),
            }
        )
    return months


def _count_by_status(db: Session, model, status_column) -> dict[str, int]:
    return {
        status or "non_renseigne": int(count or 0)
        for status, count in db.query(status_column, func.count(model.id))
        .group_by(status_column)
        .all()
    }


def _count_in_month(rows: list[datetime], bucket: dict) -> int:
    return sum(
        1
        for value in rows
        if (value_date := _as_date(value))
        and bucket["start"] <= value_date < bucket["end"]
    )


def _offer_month(offer) -> date | None:
    return _as_date(offer.date_validation) or _as_date(offer.created_at)


def _sum_validated_revenue(rows: list, bucket: dict) -> float:
    total = 0.0
    for offer in rows:
        value_date = _offer_month(offer)
        if value_date and bucket["start"] <= value_date < bucket["end"]:
            total += _money(offer.montant_total)
    return total


def _role_distribution(db: Session) -> list[dict]:
    rows = (
        db.query(Role.nom_role, func.count(Utilisateur.id_utilisateur))
        .join(Utilisateur, Utilisateur.id_role == Role.id_role)
        .group_by(Role.nom_role)
        .order_by(Role.nom_role.asc())
        .all()
    )
    return [
        {
            "role": role or "sans_role",
            "label": (role or "Sans role").replace("_", " ").title(),
            "count": int(count or 0),
        }
        for role, count in rows
    ]


def _offers_status_chart(db: Session) -> list[dict]:
    teambuilding_counts = _count_by_status(db, Offre, Offre.statut)
    tourism_counts = _count_by_status(db, OffreTourisme, OffreTourisme.statut)
    return [
        {
            "status": status,
            "label": label,
            "teambuilding": teambuilding_counts.get(status, 0),
            "tourisme": tourism_counts.get(status, 0),
        }
        for status, label in OFFER_STATUS_LABELS.items()
    ]


def _proformas_by_pole(db: Session) -> list[dict]:
    rows = (
        db.query(Proforma.pole, Proforma.statut, func.count(Proforma.id))
        .group_by(Proforma.pole, Proforma.statut)
        .all()
    )
    grouped: dict[str, dict] = {}
    for pole, statut, count in rows:
        key = pole or "teambuilding"
        grouped.setdefault(
            key,
            {
                "pole": key,
                "label": "Team building" if key == "teambuilding" else "Tourisme",
                "total": 0,
                "brouillon": 0,
                "validee": 0,
                "pdf_genere": 0,
                "annulee": 0,
            },
        )
        grouped[key]["total"] += int(count or 0)
        grouped[key][statut or "brouillon"] = int(count or 0)
    return list(grouped.values())


def _monthly_series(db: Session, buckets: list[dict]) -> list[dict]:
    start = datetime.combine(buckets[0]["start"], datetime.min.time())
    tb_dates = [
        item[0]
        for item in db.query(DemandeTeamBuilding.created_at)
        .filter(DemandeTeamBuilding.created_at >= start)
        .all()
    ]
    tourism_dates = [
        item[0]
        for item in db.query(DemandeTourisme.created_at)
        .filter(DemandeTourisme.created_at >= start)
        .all()
    ]
    custom_dates = [
        item[0]
        for item in db.query(DemandeTourismeCustom.created_at)
        .filter(DemandeTourismeCustom.created_at >= start)
        .all()
    ]
    contact_dates = [
        item[0]
        for item in db.query(DemandeContact.created_at)
        .filter(DemandeContact.created_at >= start)
        .all()
    ]

    return [
        {
            "key": bucket["key"],
            "label": bucket["label"],
            "teambuilding": _count_in_month(tb_dates, bucket),
            "tourisme_circuits": _count_in_month(tourism_dates, bucket),
            "tourisme_personnalise": _count_in_month(custom_dates, bucket),
            "contacts": _count_in_month(contact_dates, bucket),
        }
        for bucket in buckets
    ]


def _monthly_revenue(db: Session, buckets: list[dict]) -> list[dict]:
    start = datetime.combine(buckets[0]["start"], datetime.min.time())
    tb_offers = (
        db.query(Offre)
        .filter(
            Offre.statut == "validee",
            Offre.created_at >= start,
        )
        .all()
    )
    tourism_offers = (
        db.query(OffreTourisme)
        .filter(
            OffreTourisme.statut == "validee",
            OffreTourisme.created_at >= start,
        )
        .all()
    )
    return [
        {
            "key": bucket["key"],
            "label": bucket["label"],
            "teambuilding": _sum_validated_revenue(tb_offers, bucket),
            "tourisme": _sum_validated_revenue(tourism_offers, bucket),
        }
        for bucket in buckets
    ]


def _requests_distribution(db: Session) -> list[dict]:
    values = [
        ("Team building", db.query(DemandeTeamBuilding).count()),
        ("Tourisme circuits", db.query(DemandeTourisme).count()),
        ("Tourisme personnalise", db.query(DemandeTourismeCustom).count()),
        ("Contacts site", db.query(DemandeContact).count()),
    ]
    return [{"label": label, "value": int(value or 0)} for label, value in values]


def _build_alerts(db: Session, today: date) -> list[dict]:
    alerts = []

    for item in (
        db.query(DemandeContact)
        .filter(DemandeContact.statut == "nouvelle")
        .order_by(DemandeContact.created_at.asc())
        .limit(4)
        .all()
    ):
        alerts.append(
            {
                "id": f"contact-{item.id}",
                "type": "contact",
                "severity": "high",
                "title": "Contact site non traite",
                "detail": f"{item.nom_complet} - {item.type_demande}",
                "route": "/admin/demandes",
            }
        )

    for item in (
        db.query(DemandeTeamBuilding)
        .filter(DemandeTeamBuilding.statut == "nouvelle")
        .order_by(DemandeTeamBuilding.created_at.asc())
        .limit(4)
        .all()
    ):
        alerts.append(
            {
                "id": f"tb-{item.id}",
                "type": "demande",
                "severity": "high",
                "title": "Demande team building a traiter",
                "detail": f"{item.entreprise} - {item.nombre_participants} participant(s)",
                "route": "/teambuilding/demandes",
            }
        )

    for item in (
        db.query(DemandeTourisme)
        .filter(DemandeTourisme.statut == "nouvelle")
        .order_by(DemandeTourisme.created_at.asc())
        .limit(3)
        .all()
    ):
        alerts.append(
            {
                "id": f"tourisme-{item.id}",
                "type": "demande",
                "severity": "high",
                "title": "Demande tourisme circuit a traiter",
                "detail": f"{item.prenom} {item.nom} - {item.titre_circuit}",
                "route": "/tourisme/demandes-circuits",
            }
        )

    sent_limit = today - timedelta(days=7)
    for offer in (
        db.query(Offre)
        .options(selectinload(Offre.demande))
        .filter(
            Offre.statut == "envoyee",
            Offre.date_envoi.is_not(None),
            Offre.date_envoi <= sent_limit,
        )
        .order_by(Offre.date_envoi.asc())
        .limit(3)
        .all()
    ):
        alerts.append(
            {
                "id": f"offre-tb-{offer.id}",
                "type": "offre",
                "severity": "medium",
                "title": "Offre team building sans retour",
                "detail": f"{offer.reference or offer.titre} - envoyee depuis 7 jours",
                "route": "/teambuilding/offres",
            }
        )

    for material in (
        db.query(Materiel)
        .filter(
            Materiel.statut.is_not(False),
            Materiel.quantite_disponible <= LOW_STOCK_THRESHOLD,
        )
        .order_by(Materiel.quantite_disponible.asc(), Materiel.nom.asc())
        .limit(5)
        .all()
    ):
        label = " ".join(
            value
            for value in (material.marque, material.modele)
            if value
        ) or material.nom
        alerts.append(
            {
                "id": f"stock-{material.id}",
                "type": "stock",
                "severity": "high" if material.quantite_disponible == 0 else "medium",
                "title": "Stock production a surveiller",
                "detail": f"{label} - {int(material.quantite_disponible or 0)} unite(s)",
                "route": "/production/materiel",
            }
        )

    alerts.sort(key=lambda item: SEVERITY_ORDER[item["severity"]])
    return alerts[:12]


def _recent_activity(db: Session) -> list[dict]:
    rows = []

    for item in (
        db.query(DemandeTeamBuilding)
        .order_by(DemandeTeamBuilding.created_at.desc())
        .limit(5)
        .all()
    ):
        rows.append(
            {
                "id": f"tb-{item.id}",
                "module": "Team building",
                "type": "Demande",
                "client": item.entreprise,
                "details": item.objectif,
                "date": item.created_at,
                "status": item.statut,
            }
        )

    for item in (
        db.query(DemandeTourisme)
        .order_by(DemandeTourisme.created_at.desc())
        .limit(5)
        .all()
    ):
        rows.append(
            {
                "id": f"tourisme-{item.id}",
                "module": "Tourisme",
                "type": "Circuit",
                "client": f"{item.prenom} {item.nom}",
                "details": item.titre_circuit,
                "date": item.created_at,
                "status": item.statut,
            }
        )

    for item in (
        db.query(Offre)
        .order_by(Offre.created_at.desc())
        .limit(4)
        .all()
    ):
        rows.append(
            {
                "id": f"offre-tb-{item.id}",
                "module": "Team building",
                "type": "Offre",
                "client": item.titre,
                "details": item.reference or "Sans reference",
                "date": item.created_at,
                "status": item.statut,
            }
        )

    for item in (
        db.query(OffreTourisme)
        .order_by(OffreTourisme.created_at.desc())
        .limit(4)
        .all()
    ):
        rows.append(
            {
                "id": f"offre-tourisme-{item.id}",
                "module": "Tourisme",
                "type": "Offre",
                "client": item.titre,
                "details": item.reference,
                "date": item.created_at,
                "status": item.statut,
            }
        )

    for item in (
        db.query(Proforma)
        .order_by(Proforma.created_at.desc())
        .limit(4)
        .all()
    ):
        rows.append(
            {
                "id": f"proforma-{item.id}",
                "module": "Tourisme" if item.pole == "tourisme" else "Team building",
                "type": "Proforma",
                "client": item.client,
                "details": item.reference,
                "date": item.created_at,
                "status": item.statut,
            }
        )

    rows.sort(key=lambda item: _as_datetime(item["date"]), reverse=True)
    return rows[:12]


def get_dashboard(db: Session) -> dict:
    now = datetime.now()
    today = now.date()
    buckets = _last_six_months(today)

    tb_new = db.query(DemandeTeamBuilding).filter(DemandeTeamBuilding.statut == "nouvelle").count()
    tourism_new = db.query(DemandeTourisme).filter(DemandeTourisme.statut == "nouvelle").count()
    custom_new = db.query(DemandeTourismeCustom).filter(DemandeTourismeCustom.statut == "nouvelle").count()
    contact_new = db.query(DemandeContact).filter(DemandeContact.statut == "nouvelle").count()

    tb_validated_revenue = _money(
        db.query(func.coalesce(func.sum(Offre.montant_total), 0))
        .filter(Offre.statut == "validee")
        .scalar()
    )
    tourism_validated_revenue = _money(
        db.query(func.coalesce(func.sum(OffreTourisme.montant_total), 0))
        .filter(OffreTourisme.statut == "validee")
        .scalar()
    )
    low_stock_count = (
        db.query(Materiel)
        .filter(
            Materiel.statut.is_not(False),
            Materiel.quantite_disponible <= LOW_STOCK_THRESHOLD,
        )
        .count()
    )

    stats = {
        "total_users": db.query(Utilisateur).count(),
        "active_users": db.query(Utilisateur).filter(Utilisateur.actif.is_(True)).count(),
        "inactive_users": db.query(Utilisateur).filter(Utilisateur.actif.is_(False)).count(),
        "newsletter_subscribers": db.query(NewsletterSubscriber).filter(NewsletterSubscriber.actif.is_(True)).count(),
        "pending_contacts": contact_new,
        "new_requests_total": tb_new + tourism_new + custom_new + contact_new,
        "new_teambuilding_requests": tb_new,
        "new_tourism_requests": tourism_new + custom_new,
        "sent_offers": (
            db.query(Offre).filter(Offre.statut == "envoyee").count()
            + db.query(OffreTourisme).filter(OffreTourisme.statut == "envoyee").count()
        ),
        "validated_revenue": tb_validated_revenue + tourism_validated_revenue,
        "generated_proformas": db.query(Proforma).filter(Proforma.statut == "pdf_genere").count(),
        "low_stock_items": low_stock_count,
    }

    return {
        "generated_at": now,
        "stats": stats,
        "charts": {
            "monthly_labels": [bucket["label"] for bucket in buckets],
            "monthly_demands": _monthly_series(db, buckets),
            "monthly_revenue": _monthly_revenue(db, buckets),
            "requests_distribution": _requests_distribution(db),
            "offers_status": _offers_status_chart(db),
            "proformas_by_pole": _proformas_by_pole(db),
            "users_by_role": _role_distribution(db),
        },
        "alerts": _build_alerts(db, today),
        "recent_activity": _recent_activity(db),
    }
