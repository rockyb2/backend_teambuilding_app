"""
Routes pour la gestion des sites
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from crud import site as crud_site
from database.schemas import SiteCreate, SiteRead
from api.dependencies import get_db
from security import require_module_access

router = APIRouter(
    prefix="/api/sites",
    tags=["sites"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


@router.get("", response_model=List[SiteRead])
def get_sites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les sites"""
    return crud_site.get_sites(db, skip=skip, limit=limit)


@router.get("/{site_id}", response_model=SiteRead)
def get_site(site_id: int, db: Session = Depends(get_db)):
    """Récupérer un site par ID"""
    db_site = crud_site.get_site(db, site_id)
    if not db_site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return db_site


@router.post("", response_model=SiteRead, status_code=status.HTTP_201_CREATED)
def create_site(payload: SiteCreate, db: Session = Depends(get_db)):
    """Créer un nouveau site"""
    return crud_site.create_site(db, payload)


@router.put("/{site_id}", response_model=SiteRead)
def update_site(site_id: int, payload: dict, db: Session = Depends(get_db)):
    """Mettre à jour un site"""
    db_site = crud_site.get_site(db, site_id)
    if not db_site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    return crud_site.update_site(db, db_site, payload)


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(site_id: int, db: Session = Depends(get_db)):
    """Supprimer un site"""
    db_site = crud_site.get_site(db, site_id)
    if not db_site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    crud_site.delete_site(db, db_site)
