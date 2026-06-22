from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from database.models import Activite, DemandeTeamBuilding, Depense, Materiel, Offre


ACTIVE_ACTIVITY_STATUSES = ("planifier", "en_preparation", "en_cours")
LOW_STOCK_THRESHOLD = 5
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
MONTH_LABELS = {
    1: "Jan.",
    2: "Fév.",
    3: "Mars",
    4: "Avr.",
    5: "Mai",
    6: "Juin",
    7: "Juil.",
    8: "Août",
    9: "Sept.",
    10: "Oct.",
    11: "Nov.",
    12: "Déc.",
}


def _money(value) -> float:
    return float(value or 0)


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _shift_month(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    return date(month_index // 12, month_index % 12 + 1, 1)


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


def _activity_client_name(activity: Activite) -> str:
    if activity.client:
        return activity.client.entreprise or " ".join(
            value for value in (activity.client.prenom, activity.client.nom) if value
        )
    if activity.demande:
        return activity.demande.entreprise
    if activity.offre and activity.offre.demande:
        return activity.offre.demande.entreprise
    return "Client non renseigné"


def _activity_readiness(activity: Activite) -> tuple[str, list[str]]:
    missing = []
    if not activity.responsable_id:
        missing.append("responsable")
    if not activity.activite_jeux:
        missing.append("jeu")
    if not activity.activite_materiels:
        missing.append("matériel")

    if not missing:
        return "Prête", []
    return "À compléter", missing


def _upcoming_activities(db: Session, now: datetime) -> list[Activite]:
    return (
        db.query(Activite)
        .options(
            selectinload(Activite.client),
            selectinload(Activite.demande),
            selectinload(Activite.offre).selectinload(Offre.demande),
            selectinload(Activite.site),
            selectinload(Activite.responsable),
            selectinload(Activite.activite_jeux),
            selectinload(Activite.activite_materiels),
        )
        .filter(
            Activite.statut.in_(ACTIVE_ACTIVITY_STATUSES),
            Activite.date_fin >= now,
        )
        .order_by(Activite.date_debut.asc())
        .limit(10)
        .all()
    )


def _build_priorities(
    db: Session,
    upcoming_activities: list[Activite],
    low_stock: list[Materiel],
    today: date,
) -> list[dict]:
    priorities = []

    new_requests = (
        db.query(DemandeTeamBuilding)
        .filter(DemandeTeamBuilding.statut == "nouvelle")
        .order_by(DemandeTeamBuilding.created_at.asc())
        .limit(4)
        .all()
    )
    for request in new_requests:
        priorities.append(
            {
                "id": f"demande-{request.id}",
                "type": "demande",
                "severity": "high",
                "title": "Nouvelle demande à traiter",
                "detail": f"{request.entreprise} · {request.nombre_participants} participant(s)",
                "route": "/teambuilding/demandes",
                "action_label": "Traiter",
            }
        )

    expiring_offers = (
        db.query(Offre)
        .options(selectinload(Offre.demande))
        .filter(
            Offre.statut == "envoyee",
            Offre.date_expiration.is_not(None),
            Offre.date_expiration <= today + timedelta(days=7),
        )
        .order_by(Offre.date_expiration.asc())
        .limit(4)
        .all()
    )
    for offer in expiring_offers:
        expired = offer.date_expiration < today
        priorities.append(
            {
                "id": f"offre-{offer.id}",
                "type": "offre",
                "severity": "high" if expired else "medium",
                "title": "Offre expirée à relancer" if expired else "Offre bientôt expirée",
                "detail": (
                    f"{offer.reference or offer.titre} · "
                    f"{offer.demande.entreprise if offer.demande else 'Client non renseigné'}"
                ),
                "route": "/teambuilding/offres",
                "action_label": "Relancer",
            }
        )

    preparation_limit = datetime.combine(today + timedelta(days=14), datetime.max.time())
    for activity in upcoming_activities:
        readiness, missing = _activity_readiness(activity)
        if readiness == "Prête" or activity.date_debut > preparation_limit:
            continue
        priorities.append(
            {
                "id": f"activite-{activity.id}",
                "type": "activite",
                "severity": "high" if activity.date_debut.date() <= today + timedelta(days=3) else "medium",
                "title": "Activité à compléter",
                "detail": f"{activity.reference or activity.titre} · manque : {', '.join(missing)}",
                "route": "/teambuilding/seminaires",
                "action_label": "Préparer",
            }
        )

    for material in low_stock[:4]:
        priorities.append(
            {
                "id": f"materiel-{material.id}",
                "type": "materiel",
                "severity": "high" if material.quantite_disponible == 0 else "medium",
                "title": "Rupture de stock" if material.quantite_disponible == 0 else "Stock faible",
                "detail": f"{material.nom} · {material.quantite_disponible} unité(s) disponible(s)",
                "route": "/teambuilding/stock",
                "action_label": "Gérer le stock",
            }
        )

    priorities.sort(key=lambda item: SEVERITY_ORDER[item["severity"]])
    return priorities[:12]


def get_dashboard(db: Session) -> dict:
    now = datetime.now()
    today = now.date()

    upcoming_activities = _upcoming_activities(db, now)
    low_stock = (
        db.query(Materiel)
        .filter(
            Materiel.statut.is_not(False),
            Materiel.quantite_disponible <= LOW_STOCK_THRESHOLD,
        )
        .order_by(Materiel.quantite_disponible.asc(), Materiel.nom.asc())
        .all()
    )

    validated_revenue = _money(
        db.query(func.coalesce(func.sum(Offre.montant_total), 0))
        .filter(Offre.statut == "validee")
        .scalar()
    )
    total_expenses = _money(db.query(func.coalesce(func.sum(Depense.montant), 0)).scalar())
    eligible_offers = db.query(Offre).filter(
        Offre.statut.in_(("envoyee", "validee", "refusee", "expiree"))
    ).count()
    validated_offers = db.query(Offre).filter(Offre.statut == "validee").count()
    upcoming_count, upcoming_participants = (
        db.query(
            func.count(Activite.id),
            func.coalesce(func.sum(Activite.nombre_participants), 0),
        )
        .filter(
            Activite.statut.in_(ACTIVE_ACTIVITY_STATUSES),
            Activite.date_fin >= now,
        )
        .one()
    )

    stats = {
        "nouvelles_demandes": db.query(DemandeTeamBuilding).filter(
            DemandeTeamBuilding.statut == "nouvelle"
        ).count(),
        "offres_en_attente": db.query(Offre).filter(Offre.statut == "envoyee").count(),
        "activites_a_venir": int(upcoming_count or 0),
        "participants_prevus": int(upcoming_participants or 0),
        "chiffre_affaires_valide": validated_revenue,
        "depenses_totales": total_expenses,
        "marge_estimee": validated_revenue - total_expenses,
        "taux_conversion": round((validated_offers / eligible_offers) * 100, 1) if eligible_offers else 0,
    }

    month_buckets = _last_six_months(today)
    month_start = datetime.combine(month_buckets[0]["start"], datetime.min.time())
    monthly_activities = (
        db.query(Activite)
        .filter(
            Activite.date_debut >= month_start,
            Activite.statut != "annuler",
        )
        .all()
    )
    monthly_requests = (
        db.query(DemandeTeamBuilding)
        .filter(DemandeTeamBuilding.created_at >= month_start)
        .all()
    )
    monthly_activity = []
    monthly_requests_summary = []
    for bucket in month_buckets:
        planned = sum(
            1
            for activity in monthly_activities
            if activity.statut != "terminer"
            and bucket["start"] <= activity.date_debut.date() < bucket["end"]
        )
        completed = sum(
            1
            for activity in monthly_activities
            if activity.statut == "terminer"
            and bucket["start"] <= activity.date_debut.date() < bucket["end"]
        )
        monthly_activity.append(
            {
                "key": bucket["key"],
                "label": bucket["label"],
                "planifiees": planned,
                "terminees": completed,
            }
        )
        received = sum(
            1
            for request in monthly_requests
            if bucket["start"] <= request.created_at.date() < bucket["end"]
        )
        confirmed = sum(
            1
            for request in monthly_requests
            if request.statut == "confirmee"
            and bucket["start"] <= request.created_at.date() < bucket["end"]
        )
        monthly_requests_summary.append(
            {
                "key": bucket["key"],
                "label": bucket["label"],
                "recues": received,
                "confirmees": confirmed,
            }
        )

    pipeline_labels = {
        "nouvelle": "Nouvelles",
        "contactee": "Contactées",
        "devis_envoye": "Devis envoyés",
        "confirmee": "Confirmées",
        "annulee": "Annulées",
    }
    pipeline_counts = dict(
        db.query(DemandeTeamBuilding.statut, func.count(DemandeTeamBuilding.id))
        .group_by(DemandeTeamBuilding.statut)
        .all()
    )
    pipeline = [
        {
            "status": status,
            "label": label,
            "count": int(pipeline_counts.get(status, 0)),
        }
        for status, label in pipeline_labels.items()
    ]

    upcoming = []
    for activity in upcoming_activities:
        readiness, missing = _activity_readiness(activity)
        upcoming.append(
            {
                "id": activity.id,
                "reference": activity.reference,
                "titre": activity.titre,
                "client": _activity_client_name(activity),
                "site": activity.site.nom_site if activity.site else "Site non renseigné",
                "responsable": (
                    " ".join(
                        value
                        for value in (activity.responsable.prenom, activity.responsable.nom)
                        if value
                    )
                    if activity.responsable
                    else "Non affecté"
                ),
                "date_debut": activity.date_debut,
                "date_fin": activity.date_fin,
                "participants": int(activity.nombre_participants or 0),
                "statut": activity.statut,
                "preparation": readiness,
                "elements_manquants": missing,
                "nombre_jeux": len(activity.activite_jeux),
                "nombre_materiels": len(activity.activite_materiels),
            }
        )

    recent_requests = (
        db.query(DemandeTeamBuilding)
        .order_by(DemandeTeamBuilding.created_at.desc())
        .limit(6)
        .all()
    )

    return {
        "generated_at": now,
        "stats": stats,
        "priorities": _build_priorities(db, upcoming_activities, low_stock, today),
        "monthly_activity": monthly_activity,
        "monthly_requests": monthly_requests_summary,
        "pipeline": pipeline,
        "upcoming_activities": upcoming,
        "stock_alerts": [
            {
                "id": material.id,
                "nom": material.nom,
                "quantite_disponible": int(material.quantite_disponible or 0),
                "niveau": "Rupture" if material.quantite_disponible == 0 else "Stock faible",
            }
            for material in low_stock
        ],
        "recent_requests": [
            {
                "id": request.id,
                "entreprise": request.entreprise,
                "contact": request.nom_contact,
                "participants": request.nombre_participants,
                "objectif": request.objectif,
                "statut": request.statut,
                "created_at": request.created_at,
            }
            for request in recent_requests
        ],
    }
