"""
Routes pour la gestion des fournisseurs, véhicules, trajets, péages et tarifs transport.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import fournisseur_transport as crud_fournisseur_transport
from database.schemas import (
    FournisseurTransportCreate,
    FournisseurTransportRead,
    FournisseurTransportUpdate,
    PeageTransportCreate,
    PeageTransportRead,
    PeageTransportUpdate,
    TarifTransportCreate,
    TarifTransportRead,
    TarifTransportUpdate,
    TrajetTransportCreate,
    TrajetTransportRead,
    TrajetTransportUpdate,
    VehiculeTransportCreate,
    VehiculeTransportRead,
    VehiculeTransportUpdate,
)
from security import require_module_access


router = APIRouter(
    prefix="/api/fournisseurs-transport",
    tags=["fournisseurs transport"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)

vehicules_router = APIRouter(
    prefix="/api/vehicules-transport",
    tags=["vehicules transport"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)

trajets_router = APIRouter(
    prefix="/api/trajets-transport",
    tags=["trajets transport"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)

peages_router = APIRouter(
    prefix="/api/peages-transport",
    tags=["peages transport"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)

tarifs_router = APIRouter(
    prefix="/api/tarifs-transport",
    tags=["tarifs transport"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _get_fournisseur_or_404(db: Session, fournisseur_id: int):
    db_fournisseur = crud_fournisseur_transport.get_fournisseur_transport(db, fournisseur_id)
    if not db_fournisseur:
        raise HTTPException(status_code=404, detail="Fournisseur transport non trouvé")
    return db_fournisseur


def _get_vehicule_or_404(db: Session, vehicule_id: int):
    db_vehicule = crud_fournisseur_transport.get_vehicule_transport(db, vehicule_id)
    if not db_vehicule:
        raise HTTPException(status_code=404, detail="Véhicule transport non trouvé")
    return db_vehicule


def _get_trajet_or_404(db: Session, trajet_id: int):
    db_trajet = crud_fournisseur_transport.get_trajet_transport(db, trajet_id)
    if not db_trajet:
        raise HTTPException(status_code=404, detail="Trajet transport non trouvé")
    return db_trajet


def _get_peage_or_404(db: Session, peage_id: int):
    db_peage = crud_fournisseur_transport.get_peage_transport(db, peage_id)
    if not db_peage:
        raise HTTPException(status_code=404, detail="Péage transport non trouvé")
    return db_peage


def _get_tarif_or_404(db: Session, tarif_id: int):
    db_tarif = crud_fournisseur_transport.get_tarif_transport(db, tarif_id)
    if not db_tarif:
        raise HTTPException(status_code=404, detail="Tarif transport non trouvé")
    return db_tarif


def _validate_fournisseur_nom_unique(db: Session, nom: str | None, fournisseur_id: int | None = None) -> None:
    if not nom:
        return
    existing = crud_fournisseur_transport.get_fournisseur_transport_by_nom(db, nom)
    if existing and existing.id != fournisseur_id:
        raise HTTPException(status_code=409, detail="Fournisseur transport déjà existant")


def _validate_fournisseur(db: Session, fournisseur_id: int | None) -> None:
    if fournisseur_id is None:
        return
    _get_fournisseur_or_404(db, fournisseur_id)


def _validate_trajet(db: Session, trajet_id: int | None) -> None:
    if trajet_id is None:
        return
    _get_trajet_or_404(db, trajet_id)


def _validate_tarif_context(
    db: Session,
    fournisseur_id: int | None,
    vehicule_id: int | None,
    trajet_id: int | None,
) -> None:
    if fournisseur_id is None:
        raise HTTPException(status_code=422, detail="Le fournisseur est obligatoire pour un tarif")
    if vehicule_id is None:
        raise HTTPException(status_code=422, detail="Le véhicule est obligatoire pour un tarif")
    if trajet_id is None:
        raise HTTPException(status_code=422, detail="Le trajet est obligatoire pour un tarif")

    _validate_fournisseur(db, fournisseur_id)
    _validate_trajet(db, trajet_id)

    vehicule = _get_vehicule_or_404(db, vehicule_id)
    if fournisseur_id is not None and vehicule.fournisseur_id != fournisseur_id:
        raise HTTPException(
            status_code=422,
            detail="Le véhicule sélectionné n'appartient pas à ce fournisseur",
        )


@router.get("", response_model=List[FournisseurTransportRead])
def list_fournisseurs_transport(
    skip: int = 0,
    limit: int = 100,
    actif: bool | None = None,
    db: Session = Depends(get_db),
):
    """Récupérer les fournisseurs de transport."""
    return crud_fournisseur_transport.get_fournisseurs_transport(
        db,
        skip=skip,
        limit=limit,
        actif=actif,
    )


@router.get("/{fournisseur_id}", response_model=FournisseurTransportRead)
def get_fournisseur_transport(fournisseur_id: int, db: Session = Depends(get_db)):
    """Récupérer un fournisseur de transport."""
    return _get_fournisseur_or_404(db, fournisseur_id)


@router.post("", response_model=FournisseurTransportRead, status_code=status.HTTP_201_CREATED)
def create_fournisseur_transport(
    payload: FournisseurTransportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Créer un fournisseur de transport."""
    _validate_fournisseur_nom_unique(db, payload.nom)
    payload.created_by_id = getattr(current_user, "id_utilisateur", None)
    return crud_fournisseur_transport.create_fournisseur_transport(db, payload)


@router.put("/{fournisseur_id}", response_model=FournisseurTransportRead)
def update_fournisseur_transport(
    fournisseur_id: int,
    payload: FournisseurTransportUpdate,
    db: Session = Depends(get_db),
):
    """Mettre à jour un fournisseur de transport."""
    db_fournisseur = _get_fournisseur_or_404(db, fournisseur_id)
    updates = _payload_dump(payload, exclude_unset=True)
    _validate_fournisseur_nom_unique(db, updates.get("nom"), fournisseur_id=fournisseur_id)
    return crud_fournisseur_transport.update_fournisseur_transport(db, db_fournisseur, payload)


@router.delete("/{fournisseur_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fournisseur_transport(fournisseur_id: int, db: Session = Depends(get_db)):
    """Désactiver un fournisseur de transport et ses tarifs."""
    db_fournisseur = _get_fournisseur_or_404(db, fournisseur_id)
    crud_fournisseur_transport.deactivate_fournisseur_transport(db, db_fournisseur)


@router.get("/{fournisseur_id}/tarifs", response_model=List[TarifTransportRead])
def list_tarifs_by_fournisseur(
    fournisseur_id: int,
    skip: int = 0,
    limit: int = 100,
    actif: bool | None = None,
    db: Session = Depends(get_db),
):
    """Récupérer les tarifs d'un fournisseur."""
    _get_fournisseur_or_404(db, fournisseur_id)
    return crud_fournisseur_transport.get_tarifs_transport(
        db,
        skip=skip,
        limit=limit,
        fournisseur_id=fournisseur_id,
        actif=actif,
    )


@router.get("/{fournisseur_id}/vehicules", response_model=List[VehiculeTransportRead])
def list_vehicules_by_fournisseur(
    fournisseur_id: int,
    skip: int = 0,
    limit: int = 100,
    actif: bool | None = None,
    db: Session = Depends(get_db),
):
    """Récupérer les véhicules d'un fournisseur."""
    _get_fournisseur_or_404(db, fournisseur_id)
    return crud_fournisseur_transport.get_vehicules_transport(
        db,
        skip=skip,
        limit=limit,
        fournisseur_id=fournisseur_id,
        actif=actif,
    )


@vehicules_router.get("", response_model=List[VehiculeTransportRead])
def list_vehicules_transport(
    skip: int = 0,
    limit: int = 100,
    fournisseur_id: int | None = None,
    type_vehicule: str | None = None,
    actif: bool | None = None,
    db: Session = Depends(get_db),
):
    """Récupérer les véhicules de transport."""
    if fournisseur_id is not None:
        _get_fournisseur_or_404(db, fournisseur_id)
    return crud_fournisseur_transport.get_vehicules_transport(
        db,
        skip=skip,
        limit=limit,
        fournisseur_id=fournisseur_id,
        type_vehicule=type_vehicule,
        actif=actif,
    )


@vehicules_router.get("/{vehicule_id}", response_model=VehiculeTransportRead)
def get_vehicule_transport(vehicule_id: int, db: Session = Depends(get_db)):
    """Récupérer un véhicule de transport."""
    return _get_vehicule_or_404(db, vehicule_id)


@vehicules_router.post("", response_model=VehiculeTransportRead, status_code=status.HTTP_201_CREATED)
def create_vehicule_transport(
    payload: VehiculeTransportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Créer un véhicule de transport."""
    _validate_fournisseur(db, payload.fournisseur_id)
    payload.created_by_id = getattr(current_user, "id_utilisateur", None)
    return crud_fournisseur_transport.create_vehicule_transport(db, payload)


@vehicules_router.put("/{vehicule_id}", response_model=VehiculeTransportRead)
def update_vehicule_transport(
    vehicule_id: int,
    payload: VehiculeTransportUpdate,
    db: Session = Depends(get_db),
):
    """Mettre à jour un véhicule de transport."""
    db_vehicule = _get_vehicule_or_404(db, vehicule_id)
    updates = _payload_dump(payload, exclude_unset=True)
    _validate_fournisseur(db, updates.get("fournisseur_id"))
    return crud_fournisseur_transport.update_vehicule_transport(db, db_vehicule, payload)


@vehicules_router.delete("/{vehicule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicule_transport(vehicule_id: int, db: Session = Depends(get_db)):
    """Désactiver un véhicule de transport."""
    db_vehicule = _get_vehicule_or_404(db, vehicule_id)
    crud_fournisseur_transport.deactivate_vehicule_transport(db, db_vehicule)


@trajets_router.get("", response_model=List[TrajetTransportRead])
def list_trajets_transport(
    skip: int = 0,
    limit: int = 100,
    actif: bool | None = None,
    ville_depart: str | None = None,
    destination: str | None = None,
    db: Session = Depends(get_db),
):
    """Récupérer les trajets de transport."""
    return crud_fournisseur_transport.get_trajets_transport(
        db,
        skip=skip,
        limit=limit,
        actif=actif,
        ville_depart=ville_depart,
        destination=destination,
    )


@trajets_router.get("/{trajet_id}", response_model=TrajetTransportRead)
def get_trajet_transport(trajet_id: int, db: Session = Depends(get_db)):
    """Récupérer un trajet de transport."""
    return _get_trajet_or_404(db, trajet_id)


@trajets_router.post("", response_model=TrajetTransportRead, status_code=status.HTTP_201_CREATED)
def create_trajet_transport(
    payload: TrajetTransportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Créer un trajet de transport."""
    payload.created_by_id = getattr(current_user, "id_utilisateur", None)
    return crud_fournisseur_transport.create_trajet_transport(db, payload)


@trajets_router.put("/{trajet_id}", response_model=TrajetTransportRead)
def update_trajet_transport(
    trajet_id: int,
    payload: TrajetTransportUpdate,
    db: Session = Depends(get_db),
):
    """Mettre à jour un trajet de transport."""
    db_trajet = _get_trajet_or_404(db, trajet_id)
    return crud_fournisseur_transport.update_trajet_transport(db, db_trajet, payload)


@trajets_router.delete("/{trajet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trajet_transport(trajet_id: int, db: Session = Depends(get_db)):
    """Désactiver un trajet de transport."""
    db_trajet = _get_trajet_or_404(db, trajet_id)
    crud_fournisseur_transport.deactivate_trajet_transport(db, db_trajet)


@peages_router.get("", response_model=List[PeageTransportRead])
def list_peages_transport(
    skip: int = 0,
    limit: int = 100,
    actif: bool | None = None,
    classe_vehicule: str | None = None,
    db: Session = Depends(get_db),
):
    """Récupérer les péages de transport."""
    return crud_fournisseur_transport.get_peages_transport(
        db,
        skip=skip,
        limit=limit,
        actif=actif,
        classe_vehicule=classe_vehicule,
    )


@peages_router.get("/{peage_id}", response_model=PeageTransportRead)
def get_peage_transport(peage_id: int, db: Session = Depends(get_db)):
    """Récupérer un péage de transport."""
    return _get_peage_or_404(db, peage_id)


@peages_router.post("", response_model=PeageTransportRead, status_code=status.HTTP_201_CREATED)
def create_peage_transport(
    payload: PeageTransportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Créer un péage de transport."""
    payload.created_by_id = getattr(current_user, "id_utilisateur", None)
    return crud_fournisseur_transport.create_peage_transport(db, payload)


@peages_router.put("/{peage_id}", response_model=PeageTransportRead)
def update_peage_transport(
    peage_id: int,
    payload: PeageTransportUpdate,
    db: Session = Depends(get_db),
):
    """Mettre à jour un péage de transport."""
    db_peage = _get_peage_or_404(db, peage_id)
    return crud_fournisseur_transport.update_peage_transport(db, db_peage, payload)


@peages_router.delete("/{peage_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_peage_transport(peage_id: int, db: Session = Depends(get_db)):
    """Désactiver un péage de transport."""
    db_peage = _get_peage_or_404(db, peage_id)
    crud_fournisseur_transport.deactivate_peage_transport(db, db_peage)


@tarifs_router.get("", response_model=List[TarifTransportRead])
def list_tarifs_transport(
    skip: int = 0,
    limit: int = 100,
    fournisseur_id: int | None = None,
    vehicule_id: int | None = None,
    trajet_id: int | None = None,
    type_transport: str | None = None,
    actif: bool | None = None,
    statut: str | None = None,
    db: Session = Depends(get_db),
):
    """Récupérer les tarifs de transport."""
    if fournisseur_id is not None:
        _get_fournisseur_or_404(db, fournisseur_id)
    if vehicule_id is not None:
        _get_vehicule_or_404(db, vehicule_id)
    if trajet_id is not None:
        _get_trajet_or_404(db, trajet_id)
    return crud_fournisseur_transport.get_tarifs_transport(
        db,
        skip=skip,
        limit=limit,
        fournisseur_id=fournisseur_id,
        vehicule_id=vehicule_id,
        trajet_id=trajet_id,
        type_transport=type_transport,
        actif=actif,
        statut=statut,
    )


@tarifs_router.get("/{tarif_id}", response_model=TarifTransportRead)
def get_tarif_transport(tarif_id: int, db: Session = Depends(get_db)):
    """Récupérer un tarif de transport."""
    return _get_tarif_or_404(db, tarif_id)


@tarifs_router.post("", response_model=TarifTransportRead, status_code=status.HTTP_201_CREATED)
def create_tarif_transport(
    payload: TarifTransportCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Créer un tarif de transport."""
    _validate_tarif_context(db, payload.fournisseur_id, payload.vehicule_id, payload.trajet_id)
    payload.created_by_id = getattr(current_user, "id_utilisateur", None)
    return crud_fournisseur_transport.create_tarif_transport(db, payload)


@tarifs_router.put("/{tarif_id}", response_model=TarifTransportRead)
def update_tarif_transport(
    tarif_id: int,
    payload: TarifTransportUpdate,
    db: Session = Depends(get_db),
):
    """Mettre à jour un tarif de transport."""
    db_tarif = _get_tarif_or_404(db, tarif_id)
    updates = _payload_dump(payload, exclude_unset=True)
    fournisseur_id = updates.get("fournisseur_id", db_tarif.fournisseur_id)
    vehicule_id = updates.get("vehicule_id", db_tarif.vehicule_id)
    trajet_id = updates.get("trajet_id", db_tarif.trajet_id)
    _validate_tarif_context(db, fournisseur_id, vehicule_id, trajet_id)
    return crud_fournisseur_transport.update_tarif_transport(db, db_tarif, payload)


@tarifs_router.delete("/{tarif_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tarif_transport(tarif_id: int, db: Session = Depends(get_db)):
    """Désactiver un tarif de transport."""
    db_tarif = _get_tarif_or_404(db, tarif_id)
    crud_fournisseur_transport.deactivate_tarif_transport(db, db_tarif)
