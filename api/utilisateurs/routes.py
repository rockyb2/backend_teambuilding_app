"""
Routes pour la gestion des utilisateurs.
"""

from datetime import timedelta
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import utilisateur as crud_utilisateur
from database.schemas import RoleRead, UtilisateurCreate, UtilisateurRead, UtilisateurUpdate
from security import create_access_token, create_refresh_token, decode_token, get_current_user

router = APIRouter(prefix="/api/utilisateurs", tags=["utilisateurs"])


@router.get("/roles", response_model=List[RoleRead])
def get_roles(db: Session = Depends(get_db)):
    return crud_utilisateur.get_roles(db)


@router.get("", response_model=List[UtilisateurRead])
def get_utilisateurs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_utilisateur.get_utilisateurs(db, skip=skip, limit=limit)


@router.get("/actifs", response_model=List[UtilisateurRead])
def get_utilisateurs_actifs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_utilisateur.get_utilisateurs_actifs(db, skip=skip, limit=limit)


@router.get("/role/{role}", response_model=List[UtilisateurRead])
def get_utilisateurs_by_role(role: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_utilisateur.get_utilisateurs_by_role(db, role, skip=skip, limit=limit)


@router.get("/{utilisateur_id}", response_model=UtilisateurRead)
def get_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    db_utilisateur = crud_utilisateur.get_utilisateur(db, utilisateur_id)
    if not db_utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")
    return db_utilisateur


@router.post("", response_model=UtilisateurRead, status_code=status.HTTP_201_CREATED)
def create_utilisateur(payload: UtilisateurCreate, db: Session = Depends(get_db)):
    existing = crud_utilisateur.get_utilisateur_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email deja utilise")

    try:
        return crud_utilisateur.create_utilisateur(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{utilisateur_id}", response_model=UtilisateurRead)
def update_utilisateur(utilisateur_id: int, payload: UtilisateurUpdate, db: Session = Depends(get_db)):
    db_utilisateur = crud_utilisateur.get_utilisateur(db, utilisateur_id)
    if not db_utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    if payload.email and payload.email != db_utilisateur.email:
        existing = crud_utilisateur.get_utilisateur_by_email(db, payload.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email deja utilise")

    try:
        return crud_utilisateur.update_utilisateur(db, db_utilisateur, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{utilisateur_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    db_utilisateur = crud_utilisateur.get_utilisateur(db, utilisateur_id)
    if not db_utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    crud_utilisateur.delete_utilisateur(db, db_utilisateur)


@router.post("/auth/login")
def login(payload: dict = Body(...), db: Session = Depends(get_db)):
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="email et password sont obligatoires")

    utilisateur = crud_utilisateur.authenticate_utilisateur(db, email, password)
    if not utilisateur:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    user_payload = {
        "sub": str(utilisateur.id_utilisateur),
        "email": utilisateur.email,
        "role": utilisateur.role,
    }

    access_token = create_access_token(user_payload, expires_delta=timedelta(minutes=30))
    refresh_token = create_refresh_token(user_payload)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id_utilisateur": utilisateur.id_utilisateur,
            "nom": utilisateur.nom,
            "prenom": utilisateur.prenom,
            "email": utilisateur.email,
            "role": utilisateur.role,
            "id_role": utilisateur.id_role,
            "actif": utilisateur.actif,
            "date_creation": utilisateur.date_creation,
            "image_utilisateur": utilisateur.image_utilisateur,
        },
    }


@router.post("/auth/refresh")
def refresh_access_token(payload: dict = Body(...)):
    try:
        raw_refresh_token = payload.get("refresh_token")
        token_payload = decode_token(raw_refresh_token)
        user_payload = {
            "sub": token_payload.get("sub"),
            "email": token_payload.get("email"),
            "role": token_payload.get("role"),
        }
        access_token = create_access_token(user_payload, expires_delta=timedelta(minutes=30))
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expire")


@router.get("/auth/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "id_utilisateur": current_user.id_utilisateur,
        "nom": current_user.nom,
        "prenom": current_user.prenom,
        "email": current_user.email,
        "role": current_user.role,
        "id_role": current_user.id_role,
        "actif": current_user.actif,
        "image_utilisateur": current_user.image_utilisateur,
    }
