from typing import Optional

from sqlalchemy.orm import Session, selectinload

from database.models import (
    FournisseurTransport,
    PeageTransport,
    TarifTransport,
    TrajetTransport,
    VehiculeTransport,
)
from database.schemas import (
    FournisseurTransportCreate,
    FournisseurTransportUpdate,
    PeageTransportCreate,
    PeageTransportUpdate,
    TarifTransportCreate,
    TarifTransportUpdate,
    TrajetTransportCreate,
    TrajetTransportUpdate,
    VehiculeTransportCreate,
    VehiculeTransportUpdate,
)


def _model_dump(schema_obj, **kwargs):
    if isinstance(schema_obj, dict):
        return dict(schema_obj)
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def _apply_updates(db_obj, payload) -> None:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    for key, value in updates.items():
        if hasattr(db_obj, key):
            setattr(db_obj, key, value)


def get_fournisseur_transport(db: Session, fournisseur_id: int) -> Optional[FournisseurTransport]:
    return (
        db.query(FournisseurTransport)
        .options(
            selectinload(FournisseurTransport.vehicules),
            selectinload(FournisseurTransport.tarifs),
        )
        .filter(FournisseurTransport.id == fournisseur_id)
        .first()
    )


def get_fournisseur_transport_by_nom(db: Session, nom: str) -> Optional[FournisseurTransport]:
    return db.query(FournisseurTransport).filter(FournisseurTransport.nom == nom).first()


def get_fournisseurs_transport(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    actif: bool | None = None,
) -> list[FournisseurTransport]:
    query = db.query(FournisseurTransport).options(
        selectinload(FournisseurTransport.vehicules),
        selectinload(FournisseurTransport.tarifs),
    )
    if actif is not None:
        query = query.filter(FournisseurTransport.actif == actif)
    return query.order_by(FournisseurTransport.nom.asc()).offset(skip).limit(limit).all()


def create_fournisseur_transport(db: Session, payload: FournisseurTransportCreate) -> FournisseurTransport:
    db_fournisseur = FournisseurTransport(**_model_dump(payload))
    db.add(db_fournisseur)
    db.commit()
    db.refresh(db_fournisseur)
    return get_fournisseur_transport(db, db_fournisseur.id) or db_fournisseur


def update_fournisseur_transport(
    db: Session,
    db_fournisseur: FournisseurTransport,
    payload: FournisseurTransportUpdate | dict,
) -> FournisseurTransport:
    _apply_updates(db_fournisseur, payload)
    db.commit()
    db.refresh(db_fournisseur)
    return get_fournisseur_transport(db, db_fournisseur.id) or db_fournisseur


def deactivate_fournisseur_transport(db: Session, db_fournisseur: FournisseurTransport) -> None:
    db_fournisseur.actif = False
    for vehicule in db_fournisseur.vehicules:
        vehicule.actif = False
        vehicule.statut = "archive"
    for tarif in db_fournisseur.tarifs:
        tarif.actif = False
        tarif.statut = "inactif"
    db.commit()


def get_vehicule_transport(db: Session, vehicule_id: int) -> Optional[VehiculeTransport]:
    return db.query(VehiculeTransport).filter(VehiculeTransport.id == vehicule_id).first()


def get_vehicules_transport(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    fournisseur_id: int | None = None,
    type_vehicule: str | None = None,
    actif: bool | None = None,
) -> list[VehiculeTransport]:
    query = db.query(VehiculeTransport)
    if fournisseur_id is not None:
        query = query.filter(VehiculeTransport.fournisseur_id == fournisseur_id)
    if type_vehicule:
        query = query.filter(VehiculeTransport.type_vehicule == type_vehicule)
    if actif is not None:
        query = query.filter(VehiculeTransport.actif == actif)
    return (
        query.order_by(VehiculeTransport.type_vehicule.asc(), VehiculeTransport.libelle.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_vehicule_transport(db: Session, payload: VehiculeTransportCreate) -> VehiculeTransport:
    db_vehicule = VehiculeTransport(**_model_dump(payload))
    db.add(db_vehicule)
    db.commit()
    db.refresh(db_vehicule)
    return db_vehicule


def update_vehicule_transport(
    db: Session,
    db_vehicule: VehiculeTransport,
    payload: VehiculeTransportUpdate | dict,
) -> VehiculeTransport:
    _apply_updates(db_vehicule, payload)
    db.commit()
    db.refresh(db_vehicule)
    return db_vehicule


def deactivate_vehicule_transport(db: Session, db_vehicule: VehiculeTransport) -> None:
    db_vehicule.actif = False
    db_vehicule.statut = "archive"
    db.commit()


def get_trajet_transport(db: Session, trajet_id: int) -> Optional[TrajetTransport]:
    return db.query(TrajetTransport).filter(TrajetTransport.id == trajet_id).first()


def get_trajets_transport(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    actif: bool | None = None,
    ville_depart: str | None = None,
    destination: str | None = None,
) -> list[TrajetTransport]:
    query = db.query(TrajetTransport)
    if actif is not None:
        query = query.filter(TrajetTransport.actif == actif)
    if ville_depart:
        query = query.filter(TrajetTransport.ville_depart.ilike(f"%{ville_depart}%"))
    if destination:
        query = query.filter(TrajetTransport.destination.ilike(f"%{destination}%"))
    return (
        query.order_by(TrajetTransport.ville_depart.asc(), TrajetTransport.destination.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_trajet_transport(db: Session, payload: TrajetTransportCreate) -> TrajetTransport:
    db_trajet = TrajetTransport(**_model_dump(payload))
    db.add(db_trajet)
    db.commit()
    db.refresh(db_trajet)
    return db_trajet


def update_trajet_transport(
    db: Session,
    db_trajet: TrajetTransport,
    payload: TrajetTransportUpdate | dict,
) -> TrajetTransport:
    _apply_updates(db_trajet, payload)
    db.commit()
    db.refresh(db_trajet)
    return db_trajet


def deactivate_trajet_transport(db: Session, db_trajet: TrajetTransport) -> None:
    db_trajet.actif = False
    db.commit()


def get_peage_transport(db: Session, peage_id: int) -> Optional[PeageTransport]:
    return db.query(PeageTransport).filter(PeageTransport.id == peage_id).first()


def get_peages_transport(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    actif: bool | None = None,
    classe_vehicule: str | None = None,
) -> list[PeageTransport]:
    query = db.query(PeageTransport)
    if actif is not None:
        query = query.filter(PeageTransport.actif == actif)
    if classe_vehicule:
        query = query.filter(PeageTransport.classe_vehicule == classe_vehicule)
    return (
        query.order_by(PeageTransport.nom_poste.asc(), PeageTransport.classe_vehicule.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_peage_transport(db: Session, payload: PeageTransportCreate) -> PeageTransport:
    db_peage = PeageTransport(**_model_dump(payload))
    db.add(db_peage)
    db.commit()
    db.refresh(db_peage)
    return db_peage


def update_peage_transport(
    db: Session,
    db_peage: PeageTransport,
    payload: PeageTransportUpdate | dict,
) -> PeageTransport:
    _apply_updates(db_peage, payload)
    db.commit()
    db.refresh(db_peage)
    return db_peage


def deactivate_peage_transport(db: Session, db_peage: PeageTransport) -> None:
    db_peage.actif = False
    db.commit()


def get_tarif_transport(db: Session, tarif_id: int) -> Optional[TarifTransport]:
    return db.query(TarifTransport).filter(TarifTransport.id == tarif_id).first()


def get_tarifs_transport(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    fournisseur_id: int | None = None,
    vehicule_id: int | None = None,
    trajet_id: int | None = None,
    type_transport: str | None = None,
    actif: bool | None = None,
    statut: str | None = None,
) -> list[TarifTransport]:
    query = db.query(TarifTransport)
    if fournisseur_id is not None:
        query = query.filter(TarifTransport.fournisseur_id == fournisseur_id)
    if vehicule_id is not None:
        query = query.filter(TarifTransport.vehicule_id == vehicule_id)
    if trajet_id is not None:
        query = query.filter(TarifTransport.trajet_id == trajet_id)
    if type_transport:
        query = query.filter(TarifTransport.type_transport == type_transport)
    if actif is not None:
        query = query.filter(TarifTransport.actif == actif)
    if statut:
        query = query.filter(TarifTransport.statut == statut)
    return (
        query.order_by(
            TarifTransport.type_transport.asc(),
            TarifTransport.libelle.asc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_tarif_transport(db: Session, payload: TarifTransportCreate) -> TarifTransport:
    db_tarif = TarifTransport(**_model_dump(payload))
    db.add(db_tarif)
    db.commit()
    db.refresh(db_tarif)
    return db_tarif


def update_tarif_transport(
    db: Session,
    db_tarif: TarifTransport,
    payload: TarifTransportUpdate | dict,
) -> TarifTransport:
    _apply_updates(db_tarif, payload)
    db.commit()
    db.refresh(db_tarif)
    return db_tarif


def deactivate_tarif_transport(db: Session, db_tarif: TarifTransport) -> None:
    db_tarif.actif = False
    db_tarif.statut = "inactif"
    db.commit()
