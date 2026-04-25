from typing import Optional

from sqlalchemy.orm import Session

from database.models import Role, Utilisateur
from database.schemas import UtilisateurCreate, UtilisateurUpdate
from security import get_password_hash, verify_password


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def _resolve_role_id(db: Session, role: Optional[str] = None, id_role: Optional[int] = None) -> int:
    if id_role is not None:
        db_role = db.query(Role).filter(Role.id_role == id_role).first()
        if not db_role:
            raise ValueError("Role introuvable")
        return db_role.id_role

    # We intentionally require an explicit role choice during user creation.
    # It avoids accidentally creating privileged accounts with an implicit default.
    role_name = role
    if not role_name:
        raise ValueError("Un role explicite est obligatoire")

    db_role = db.query(Role).filter(Role.nom_role == role_name).first()
    if not db_role:
        raise ValueError(f"Role '{role_name}' introuvable")
    return db_role.id_role


def get_utilisateur(db: Session, utilisateur_id: int) -> Optional[Utilisateur]:
    return db.query(Utilisateur).filter(Utilisateur.id_utilisateur == utilisateur_id).first()


def get_utilisateur_by_email(db: Session, email: str) -> Optional[Utilisateur]:
    return db.query(Utilisateur).filter(Utilisateur.email == email).first()


def get_utilisateurs(db: Session, skip: int = 0, limit: int = 100) -> list[Utilisateur]:
    return db.query(Utilisateur).offset(skip).limit(limit).all()


def get_utilisateurs_actifs(db: Session, skip: int = 0, limit: int = 100) -> list[Utilisateur]:
    return db.query(Utilisateur).filter(Utilisateur.actif == True).offset(skip).limit(limit).all()


def get_utilisateurs_by_role(db: Session, role: str, skip: int = 0, limit: int = 100) -> list[Utilisateur]:
    return (
        db.query(Utilisateur)
        .join(Utilisateur.role_rel)
        .filter(Role.nom_role == role)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_roles(db: Session) -> list[Role]:
    return db.query(Role).order_by(Role.nom_role.asc()).all()


def create_utilisateur(db: Session, payload: UtilisateurCreate) -> Utilisateur:
    data = _model_dump(payload)
    mot_de_passe = data.pop("mot_de_passe")
    role_name = data.pop("role", None)
    role_id = data.pop("id_role", None)
    data["id_role"] = _resolve_role_id(db, role=role_name, id_role=role_id)

    db_utilisateur = Utilisateur(**data)
    db_utilisateur.mot_de_passe = get_password_hash(mot_de_passe)

    db.add(db_utilisateur)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur


def update_utilisateur(db: Session, db_utilisateur: Utilisateur, payload: UtilisateurUpdate) -> Utilisateur:
    updates = _model_dump(payload, exclude_unset=True)

    has_role_name = "role" in updates
    has_role_id = "id_role" in updates
    role_name = updates.pop("role", None)
    role_id = updates.pop("id_role", None)

    if has_role_name or has_role_id:
        db_utilisateur.id_role = _resolve_role_id(db, role=role_name, id_role=role_id)

    for key, value in updates.items():
        setattr(db_utilisateur, key, value)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur


def delete_utilisateur(db: Session, db_utilisateur: Utilisateur) -> None:
    db.delete(db_utilisateur)
    db.commit()


def authenticate_utilisateur(db: Session, email: str, password: str) -> Optional[Utilisateur]:
    utilisateur = get_utilisateur_by_email(db, email)
    if utilisateur and verify_password(password, utilisateur.mot_de_passe):
        return utilisateur
    return None
