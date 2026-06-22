"""
Routes pour la gestion des activites team building.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import activite as crud_activite
from crud import activite_materiel as crud_activite_materiel
from crud import client as crud_client
from crud import demande_team_building as crud_demande_team_building
from crud import offre as crud_offre
from crud import personnel as crud_personnel
from crud import site as crud_site
from database.schemas import ActiviteCreate, ActiviteRead, ActiviteUpdate
from security import require_module_access

router = APIRouter(
    prefix="/api/activites",
    tags=["activites"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _validate_activite_relations(db: Session, data: dict):
    if data.get("client_id") is not None and not crud_client.get_client(db, data["client_id"]):
        raise HTTPException(status_code=404, detail="Client non trouve")

    if data.get("demande_id") is not None:
        demande = crud_demande_team_building.get_demande_team_building(db, data["demande_id"])
        if not demande:
            raise HTTPException(status_code=404, detail="Demande non trouvee")

    if data.get("offre_id") is not None:
        offre = crud_offre.get_offre(db, data["offre_id"])
        if not offre:
            raise HTTPException(status_code=404, detail="Offre non trouvee")
        if offre.statut not in crud_offre.OFFRE_STATUSES_ELIGIBLES_ACTIVITE:
            raise HTTPException(
                status_code=400,
                detail="Seule une offre validee peut etre liee a une activite",
            )

    if data.get("site_id") is not None and not crud_site.get_site(db, data["site_id"]):
        raise HTTPException(status_code=404, detail="Site non trouve")

    if data.get("responsable_id") is not None:
        responsable = crud_personnel.get_personnel(db, data["responsable_id"])
        if not responsable:
            raise HTTPException(status_code=404, detail="Responsable non trouve")


def _validate_offre_available(db: Session, offre_id: int | None, exclude_activite_id: int | None = None):
    if offre_id is None:
        return

    activite_existante = crud_activite.get_activite_by_offre(db, offre_id)
    if activite_existante and activite_existante.id != exclude_activite_id:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cette offre est deja liee a l'activite "
                f"{activite_existante.reference or activite_existante.titre}"
            ),
        )


def _apply_demande_participants_default(db: Session, data: dict, payload=None):
    if data.get("demande_id") is None or data.get("nombre_participants") is not None:
        return

    demande = crud_demande_team_building.get_demande_team_building(db, data["demande_id"])
    if demande and demande.nombre_participants:
        data["nombre_participants"] = demande.nombre_participants
        if payload is not None:
            payload.nombre_participants = demande.nombre_participants


def _integrity_error_detail(error: IntegrityError) -> str:
    constraint_name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
    if constraint_name == "activite_id_offre_key":
        return "Cette offre est deja liee a une autre activite"
    if constraint_name in {"activite_reference_key", "ix_activite_reference"}:
        return "Une activite possede deja cette reference"
    return "Impossible d'enregistrer l'activite a cause d'une contrainte de la base de donnees"


@router.get("", response_model=List[ActiviteRead])
def get_activites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer toutes les activites."""
    return crud_activite.get_activites(db, skip=skip, limit=limit)


@router.get("/offres/{offre_id}", response_model=ActiviteRead)
def get_activite_by_offre(offre_id: int, db: Session = Depends(get_db)):
    """Recuperer l'unique activite liee a une offre."""
    if not crud_offre.get_offre(db, offre_id):
        raise HTTPException(status_code=404, detail="Offre non trouvee")

    db_activite = crud_activite.get_activite_by_offre(db, offre_id)
    if not db_activite:
        raise HTTPException(status_code=404, detail="Aucune activite liee a cette offre")
    return db_activite


@router.get("/demandes/{demande_id}", response_model=List[ActiviteRead])
def get_activites_by_demande(demande_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les activites liees a une demande."""
    demande = crud_demande_team_building.get_demande_team_building(db, demande_id)
    if not demande:
        raise HTTPException(status_code=404, detail="Demande non trouvee")

    return crud_activite.get_activites_by_demande(db, demande_id, skip=skip, limit=limit)


@router.get("/clients/{client_id}", response_model=List[ActiviteRead])
def get_activites_by_client(client_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les activites liees a un client."""
    if not crud_client.get_client(db, client_id):
        raise HTTPException(status_code=404, detail="Client non trouve")

    return crud_activite.get_activites_by_client(db, client_id, skip=skip, limit=limit)


@router.get("/sites/{site_id}", response_model=List[ActiviteRead])
def get_activites_by_site(site_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les activites d'un site."""
    if not crud_site.get_site(db, site_id):
        raise HTTPException(status_code=404, detail="Site non trouve")

    return crud_activite.get_activites_by_site(db, site_id, skip=skip, limit=limit)


@router.get("/responsables/{responsable_id}", response_model=List[ActiviteRead])
def get_activites_by_responsable(
    responsable_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Recuperer les activites d'un responsable."""
    if not crud_personnel.get_personnel(db, responsable_id):
        raise HTTPException(status_code=404, detail="Responsable non trouve")

    return crud_activite.get_activites_by_responsable(db, responsable_id, skip=skip, limit=limit)


@router.get("/{activite_id}", response_model=ActiviteRead)
def get_activite(activite_id: int, db: Session = Depends(get_db)):
    """Recuperer une activite par ID."""
    db_activite = crud_activite.get_activite(db, activite_id)
    if not db_activite:
        raise HTTPException(status_code=404, detail="Activite non trouvee")
    return db_activite


@router.post("", response_model=ActiviteRead, status_code=status.HTTP_201_CREATED)
def create_activite(
    payload: ActiviteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Creer une nouvelle activite."""
    payload.id_utilisateur_create = getattr(current_user, "id_utilisateur", None)
    data = _payload_dump(payload)
    _validate_activite_relations(db, data)
    _apply_demande_participants_default(db, data, payload)
    _validate_offre_available(db, data.get("offre_id"))
    if data["date_fin"] <= data["date_debut"]:
        raise HTTPException(status_code=400, detail="La date de fin doit etre apres la date de debut")

    try:
        return crud_activite.create_activite(db, payload)
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail=_integrity_error_detail(error)) from error


@router.put("/{activite_id}", response_model=ActiviteRead)
def update_activite(activite_id: int, payload: ActiviteUpdate, db: Session = Depends(get_db)):
    """Mettre a jour une activite."""
    db_activite = crud_activite.get_activite(db, activite_id)
    if not db_activite:
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    updates = _payload_dump(payload, exclude_unset=True)
    _validate_activite_relations(db, updates)
    final_demande_id = updates.get("demande_id", db_activite.demande_id)
    final_participants = updates.get("nombre_participants", db_activite.nombre_participants)
    if final_participants is None:
        default_data = {"demande_id": final_demande_id, "nombre_participants": None}
        _apply_demande_participants_default(db, default_data)
        if default_data.get("nombre_participants") is not None:
            updates["nombre_participants"] = default_data["nombre_participants"]
    offre_id = updates.get("offre_id", db_activite.offre_id)
    _validate_offre_available(db, offre_id, exclude_activite_id=db_activite.id)

    date_debut = updates.get("date_debut", db_activite.date_debut)
    date_fin = updates.get("date_fin", db_activite.date_fin)
    statut_activite = updates.get("statut", db_activite.statut)
    if date_fin <= date_debut:
        raise HTTPException(status_code=400, detail="La date de fin doit etre apres la date de debut")

    if crud_activite_materiel.activite_reserve_materiel(statut_activite):
        affectations_materiel = crud_activite_materiel.get_materiels_by_activite(db, db_activite.id)
        for affectation in sorted(affectations_materiel, key=lambda item: item.materiel_id):
            if affectation.materiel.statut is False:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Impossible de modifier l'activite: {affectation.materiel.nom} "
                        "est un materiel inactif"
                    ),
                )
            crud_activite_materiel.lock_materiel_reservation(db, affectation.materiel_id)
            quantite_disponible = crud_activite_materiel.get_quantite_disponible(
                db,
                affectation.materiel,
                date_debut,
                date_fin,
                exclude_activite_id=db_activite.id,
            )
            if affectation.quantite_prevue > quantite_disponible:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Impossible de modifier l'activite: {affectation.materiel.nom} "
                        f"necessite {affectation.quantite_prevue}, mais seulement "
                        f"{quantite_disponible} disponible(s) sur cette periode"
                    ),
                )

    try:
        return crud_activite.update_activite(db, db_activite, updates)
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail=_integrity_error_detail(error)) from error


@router.delete("/{activite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activite(activite_id: int, db: Session = Depends(get_db)):
    """Supprimer une activite."""
    db_activite = crud_activite.get_activite(db, activite_id)
    if not db_activite:
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    crud_activite.delete_activite(db, db_activite)
