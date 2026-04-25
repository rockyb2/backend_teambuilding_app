"""
Routes pour la gestion des roles.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import role as crud_role
from database.schemas import RoleCreate, RoleRead, RoleUpdate
from security import require_role_management_access, require_user_management_access

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=List[RoleRead])
def get_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_user_management_access),
):
    return crud_role.get_roles(db, skip=skip, limit=limit)


@router.get("/{role_id}", response_model=RoleRead)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_user_management_access),
):
    db_role = crud_role.get_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role non trouve")
    return db_role


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role_management_access),
):
    existing = crud_role.get_role_by_name(db, payload.nom_role)
    if existing:
        raise HTTPException(status_code=400, detail="Ce role existe deja")
    return crud_role.create_role(db, payload)


@router.put("/{role_id}", response_model=RoleRead)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role_management_access),
):
    db_role = crud_role.get_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role non trouve")

    if payload.nom_role and payload.nom_role != db_role.nom_role:
        existing = crud_role.get_role_by_name(db, payload.nom_role)
        if existing:
            raise HTTPException(status_code=400, detail="Ce role existe deja")

    return crud_role.update_role(db, db_role, payload)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role_management_access),
):
    db_role = crud_role.get_role(db, role_id)
    if not db_role:
        raise HTTPException(status_code=404, detail="Role non trouve")

    try:
        crud_role.delete_role(db, db_role)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer ce role car il est encore utilise par un ou plusieurs utilisateurs",
        )
