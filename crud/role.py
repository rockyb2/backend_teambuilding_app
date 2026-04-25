from typing import Optional

from sqlalchemy.orm import Session

from database.models import Role
from database.schemas import RoleCreate, RoleUpdate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_role(db: Session, role_id: int) -> Optional[Role]:
    return db.query(Role).filter(Role.id_role == role_id).first()


def get_role_by_name(db: Session, nom_role: str) -> Optional[Role]:
    return db.query(Role).filter(Role.nom_role == nom_role).first()


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> list[Role]:
    return db.query(Role).order_by(Role.nom_role.asc()).offset(skip).limit(limit).all()


def create_role(db: Session, payload: RoleCreate) -> Role:
    db_role = Role(**_model_dump(payload))
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


def update_role(db: Session, db_role: Role, payload: RoleUpdate) -> Role:
    updates = _model_dump(payload, exclude_unset=True)
    for key, value in updates.items():
        setattr(db_role, key, value)
    db.commit()
    db.refresh(db_role)
    return db_role


def delete_role(db: Session, db_role: Role) -> None:
    db.delete(db_role)
    db.commit()
