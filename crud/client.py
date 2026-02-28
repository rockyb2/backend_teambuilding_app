from typing import Optional

from sqlalchemy.orm import Session

from database.models import Client
from database.schemas import ClientCreate, ClientUpdate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_client(db: Session, client_id: int) -> Optional[Client]:
    return db.query(Client).filter(Client.id_client == client_id).first()


def get_client_by_email(db: Session, email: str) -> Optional[Client]:
    return db.query(Client).filter(Client.email == email).first()


def get_clients(db: Session, skip: int = 0, limit: int = 100) -> list[Client]:
    return db.query(Client).offset(skip).limit(limit).all()


def create_client(db: Session, payload: ClientCreate) -> Client:
    db_client = Client(**_model_dump(payload))
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def update_client(db: Session, db_client: Client, payload: ClientUpdate) -> Client:
    updates = _model_dump(payload, exclude_unset=True)
    for key, value in updates.items():
        setattr(db_client, key, value)

    db.commit()
    db.refresh(db_client)
    return db_client


def delete_client(db: Session, db_client: Client) -> None:
    db.delete(db_client)
    db.commit()
