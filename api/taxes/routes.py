from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.dependencies import get_db
from crud import taxe as crud_taxe
from database.schemas import TaxeCreate, TaxeRead, TaxeUpdate
from security import get_current_user, require_user_management_access

router = APIRouter(prefix="/api/taxes", tags=["taxes"])

@router.get("", response_model=list[TaxeRead])
def list_taxes(actifs_only: bool = False, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return crud_taxe.list_taxes(db, actifs_only)

@router.get("/{taxe_id}", response_model=TaxeRead)
def get_taxe(taxe_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    taxe = crud_taxe.get_taxe(db, taxe_id)
    if not taxe: raise HTTPException(404, "Taxe non trouvée")
    return taxe

@router.post("", response_model=TaxeRead, status_code=status.HTTP_201_CREATED)
def create_taxe(payload: TaxeCreate, db: Session = Depends(get_db), _=Depends(require_user_management_access)):
    if any(t.code == payload.code for t in crud_taxe.list_taxes(db)):
        raise HTTPException(409, "Code de taxe déjà utilisé")
    return crud_taxe.create_taxe(db, payload)

@router.put("/{taxe_id}", response_model=TaxeRead)
def update_taxe(taxe_id: int, payload: TaxeUpdate, db: Session = Depends(get_db), _=Depends(require_user_management_access)):
    taxe = crud_taxe.get_taxe(db, taxe_id)
    if not taxe: raise HTTPException(404, "Taxe non trouvée")
    return crud_taxe.update_taxe(db, taxe, payload)

@router.delete("/{taxe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_taxe(taxe_id: int, db: Session = Depends(get_db), _=Depends(require_user_management_access)):
    taxe = crud_taxe.get_taxe(db, taxe_id)
    if not taxe: raise HTTPException(404, "Taxe non trouvée")
    crud_taxe.delete_taxe(db, taxe)
