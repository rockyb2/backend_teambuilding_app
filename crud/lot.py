from sqlalchemy.orm import Session
from database.models import Lot
from database.schemas import LotCreate

def create_lot(db: Session, lot: LotCreate):
    new_lot = Lot(
        nom=lot.nom,
        description=lot.description,
        quantite=lot.quantite,
        disponible=lot.disponible
    )
    db.add(new_lot)
    db.commit()
    db.refresh(new_lot)
    return new_lot

def get_all_lots(db: Session):
    return db.query(Lot).filter(Lot.disponible == True).all()

def get_lot(db: Session, lot_id: int):
    return db.query(Lot).filter(Lot.id == lot_id).first()

def update_lot_disponibilite(db: Session, lot_id: int, disponible: bool):
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if lot:
        lot.disponible = disponible
        db.commit()
        db.refresh(lot)
    return lot