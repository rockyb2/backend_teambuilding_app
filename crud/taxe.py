from sqlalchemy.orm import Session
from database.models import Taxe
from database.schemas import TaxeCreate, TaxeUpdate

def list_taxes(db: Session, actifs_only: bool = False):
    query = db.query(Taxe).order_by(Taxe.nom.asc())
    if actifs_only:
        query = query.filter(Taxe.actif.is_(True))
    return query.all()

def get_taxe(db: Session, taxe_id: int):
    return db.query(Taxe).filter(Taxe.id == taxe_id).first()

def create_taxe(db: Session, payload: TaxeCreate):
    taxe = Taxe(**payload.model_dump() if hasattr(payload, "model_dump") else payload.dict())
    db.add(taxe); db.commit(); db.refresh(taxe)
    return taxe

def update_taxe(db: Session, taxe: Taxe, payload: TaxeUpdate):
    values = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    for key, value in values.items(): setattr(taxe, key, value)
    db.commit(); db.refresh(taxe)
    return taxe

def delete_taxe(db: Session, taxe: Taxe):
    db.delete(taxe); db.commit()
