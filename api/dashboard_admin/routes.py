from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import dashboard_admin as crud_dashboard
from security import require_module_access


router = APIRouter(
    prefix="/api/dashboard/admin",
    tags=["dashboard admin"],
    dependencies=[Depends(require_module_access("administration"))],
)


@router.get("")
def get_dashboard_admin(db: Session = Depends(get_db)):
    """Retourner les indicateurs globaux reels du CRM."""
    return crud_dashboard.get_dashboard(db)
