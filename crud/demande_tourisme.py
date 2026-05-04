from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.models import (
    DemandeTourisme,
    DemandeTourismeCustom,
    HistoriqueStatutDemandeTourisme,
)
from database.schemas import (
    DemandeTourismeCreate,
    DemandeTourismeCustumerCreate,
    STATUTS_DEMANDE_TOURISME,
)


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


def get_demande_tourisme_custom(
    db: Session, demande_id: int
) -> Optional[DemandeTourismeCustom]:
    return db.query(DemandeTourismeCustom).filter(DemandeTourismeCustom.id == demande_id).first()


def get_demandes_tourisme(db: Session, skip: int = 0, limit: int = 100) -> list[DemandeTourisme]:
    return (
        db.query(DemandeTourisme)
        .order_by(DemandeTourisme.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_demandes_tourisme_custom(
    db: Session, skip: int = 0, limit: int = 100
) -> list[DemandeTourismeCustom]:
    return (
        db.query(DemandeTourismeCustom)
        .order_by(DemandeTourismeCustom.created_at.desc())
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


def update_demande_tourisme(
    db: Session,
    db_demande: DemandeTourisme,
    payload: DemandeTourismeCreate | dict,
) -> DemandeTourisme:
    data = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)

    for key, value in data.items():
        if hasattr(db_demande, key):
            setattr(db_demande, key, value)

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


def update_demande_tourisme_custom(
    db: Session,
    db_demande: DemandeTourismeCustom,
    payload: DemandeTourismeCustumerCreate | dict,
) -> DemandeTourismeCustom:
    data = _normalize_custom_tourism_payload(payload)

    for key, value in data.items():
        if hasattr(db_demande, key):
            setattr(db_demande, key, value)

    db.commit()
    db.refresh(db_demande)
    return db_demande


def _ensure_valid_statut(statut: str) -> None:
    if statut not in STATUTS_DEMANDE_TOURISME:
        raise ValueError("Statut de demande tourisme invalide")


def update_demande_tourisme_statut(
    db: Session,
    db_demande: DemandeTourisme,
    nouveau_statut: str,
    utilisateur_id: int | None,
    commentaire: str | None = None,
) -> DemandeTourisme:
    _ensure_valid_statut(nouveau_statut)
    ancien_statut = db_demande.statut

    if ancien_statut == nouveau_statut:
        return db_demande

    modifie_le = datetime.utcnow()
    db_demande.statut = nouveau_statut
    db_demande.statut_modifie_le = modifie_le
    db_demande.statut_modifie_par_id = utilisateur_id
    db.add(
        HistoriqueStatutDemandeTourisme(
            demande_tourisme_id=db_demande.id,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            commentaire=commentaire,
            modifie_par_id=utilisateur_id,
            modifie_le=modifie_le,
        )
    )
    db.commit()
    db.refresh(db_demande)
    return db_demande


def update_demande_tourisme_custom_statut(
    db: Session,
    db_demande: DemandeTourismeCustom,
    nouveau_statut: str,
    utilisateur_id: int | None,
    commentaire: str | None = None,
) -> DemandeTourismeCustom:
    _ensure_valid_statut(nouveau_statut)
    ancien_statut = db_demande.statut

    if ancien_statut == nouveau_statut:
        return db_demande

    modifie_le = datetime.utcnow()
    db_demande.statut = nouveau_statut
    db_demande.statut_modifie_le = modifie_le
    db_demande.statut_modifie_par_id = utilisateur_id
    db.add(
        HistoriqueStatutDemandeTourisme(
            demande_tourisme_custom_id=db_demande.id,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            commentaire=commentaire,
            modifie_par_id=utilisateur_id,
            modifie_le=modifie_le,
        )
    )
    db.commit()
    db.refresh(db_demande)
    return db_demande


def get_historique_demande_tourisme(
    db: Session, demande_id: int
) -> list[HistoriqueStatutDemandeTourisme]:
    return (
        db.query(HistoriqueStatutDemandeTourisme)
        .filter(HistoriqueStatutDemandeTourisme.demande_tourisme_id == demande_id)
        .order_by(HistoriqueStatutDemandeTourisme.modifie_le.desc())
        .all()
    )


def get_historique_demande_tourisme_custom(
    db: Session, demande_id: int
) -> list[HistoriqueStatutDemandeTourisme]:
    return (
        db.query(HistoriqueStatutDemandeTourisme)
        .filter(HistoriqueStatutDemandeTourisme.demande_tourisme_custom_id == demande_id)
        .order_by(HistoriqueStatutDemandeTourisme.modifie_le.desc())
        .all()
    )


def delete_demande_tourisme(db: Session, db_demande: DemandeTourisme) -> None:
    db.delete(db_demande)
    db.commit()


def delete_demande_tourisme_custom(db: Session, db_demande: DemandeTourismeCustom) -> None:
    db.delete(db_demande)
    db.commit()
