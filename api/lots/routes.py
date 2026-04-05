from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.schemas import LotCreate, LotResponse
from crud.lot import create_lot, get_all_lots, get_lot, update_lot_disponibilite
from crud.contact_akan import get_all_contacts_akan
import random
from typing import List, Dict

router = APIRouter(prefix="/lots", tags=["Lots"])

@router.post("/ajouter", response_model=LotResponse)
def create_lot_endpoint(lot: LotCreate, db: Session = Depends(get_db)):
    return create_lot(db, lot)

@router.get("/liste", response_model=List[LotResponse])
def list_lots(db: Session = Depends(get_db)):
    return get_all_lots(db)

@router.get("/{lot_id}", response_model=LotResponse)
def read_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = get_lot(db, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot introuvable")
    return lot

@router.post("/tirage-au-sort")
def effectuer_tirage_au_sort(db: Session = Depends(get_db)):
    """
    Effectue un tirage au sort parmi tous les contacts inscrits.
    Pour chaque lot disponible, tire au sort un gagnant unique.
    """
    # Récupérer tous les contacts et lots disponibles
    contacts = get_all_contacts_akan(db)
    lots = get_all_lots(db)
    
    if not contacts:
        raise HTTPException(status_code=400, detail="Aucun contact inscrit")
    
    if not lots:
        raise HTTPException(status_code=400, detail="Aucun lot disponible")
    
    # Liste des gagnants pour éviter les doublons
    gagnants_ids = set()
    resultats = []
    
    for lot in lots:
        # Filtrer les contacts qui n'ont pas encore gagné
        contacts_disponibles = [c for c in contacts if c.id not in gagnants_ids]
        
        if not contacts_disponibles:
            # Plus de contacts disponibles, arrêter le tirage
            break
        
        # Tirer au sort un gagnant
        gagnant = random.choice(contacts_disponibles)
        gagnants_ids.add(gagnant.id)
        
        resultats.append({
            "lot": {
                "id": lot.id,
                "nom": lot.nom,
                "description": lot.description
            },
            "gagnant": {
                "id": gagnant.id,
                "nom": gagnant.nom,
                "prenoms": gagnant.prenoms,
                "email": gagnant.email,
                "telephone": gagnant.telephone
            }
        })
        
        # Marquer le lot comme indisponible (optionnel, selon les règles)
        # update_lot_disponibilite(db, lot.id, False)
    
    return {
        "message": f"Tirage au sort effectué avec succès ! {len(resultats)} gagnants sélectionnés.",
        "resultats": resultats
    }