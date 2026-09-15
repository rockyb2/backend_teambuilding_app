from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud.event import create_inscription
from database.event_models import Event, InscriptionEvent
from database.event_schemas import EventRead, InscriptionEventCreate, InscriptionEventRead, InscriptionEventReceipt
from security import require_module_access

router = APIRouter(prefix='/api/events', tags=['événements'])


@router.get('/public', response_model=list[EventRead])
def public_events(db: Session = Depends(get_db)):
    return db.query(Event).order_by(Event.date.asc().nullslast(), Event.id).all()


@router.post('/inscriptions', response_model=InscriptionEventReceipt, status_code=201)
def register_contact(payload: InscriptionEventCreate, db: Session = Depends(get_db)):
    return create_inscription(db, payload)


@router.get('/inscriptions', response_model=list[InscriptionEventRead])
def list_inscriptions(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), user=Depends(require_module_access('tourisme'))):
    return db.query(InscriptionEvent).order_by(InscriptionEvent.date_inscription.desc()).offset(skip).limit(limit).all()