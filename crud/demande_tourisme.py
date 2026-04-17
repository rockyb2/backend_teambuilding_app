from typing import Optional

from sqlalchemy.orm import Session

from database.models import DemandeTourisme,DemandeTourismeCustom
from database.schemas import DemandeTourismeCreate, DemandeTourismeCustumerCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def _normalize_custom_tourism_payload(payload) -> dict:
    data = _model_dump(payload) if not isinstance(payload, dict) else dict(payload)

    return {
        "nom_client": data.get("nom") or data.get("nom_client"),
        "prenoms_client": data.get("prenom") or data.get("prenoms") or data.get("prenoms_client"),
        "email_client": data.get("email") or data.get("email_client"),
        "numero_telephone_client": data.get("telephone") or data.get("numero_telephone_client"),
        "nombre_personne": (
            data.get("nb_personnes")
            or data.get("nombre_personnes")
            or data.get("nombre_personne")
            or 1
        ),
        "nombre_jours": data.get("nb_jours") or data.get("nombre_jours"),
        "lieu_souhaite": data.get("lieu_souhaite"),
        "attente_voyage": data.get("attente_voyage"),
        "statut": data.get("statut") or "nouvelle",
    }


def get_demande_tourisme(db: Session, demande_id: int) -> Optional[DemandeTourisme]:
    return db.query(DemandeTourisme).filter(DemandeTourisme.id == demande_id).first()


def get_demandes_tourisme(db: Session, skip: int = 0, limit: int = 100) -> list[DemandeTourisme]:
    return (
        db.query(DemandeTourisme)
        .order_by(DemandeTourisme.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_demande_tourisme(db: Session, payload: DemandeTourismeCreate) -> DemandeTourisme:
    db_demande = DemandeTourisme(**_model_dump(payload))
    db.add(db_demande)
    db.commit()
    db.refresh(db_demande)
    return db_demande


def create_demande_tourisme_custom(
    db: Session, payload: DemandeTourismeCustumerCreate | dict
) -> DemandeTourismeCustom:
    db_demande = DemandeTourismeCustom(**_normalize_custom_tourism_payload(payload))
    db.add(db_demande)
    db.commit()
    db.refresh(db_demande)
    return db_demande
