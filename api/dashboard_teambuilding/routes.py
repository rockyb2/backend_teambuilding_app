from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import dashboard_teambuilding as crud_dashboard
from security import can_view_financials, get_current_user, require_module_access

router = APIRouter(
    prefix="/api/dashboard/teambuilding",
    tags=["dashboard teambuilding"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


@router.get("")
def get_dashboard_teambuilding(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Retourner les indicateurs opérationnels réels du module Team Building."""
    return crud_dashboard.get_dashboard(db, include_financials=can_view_financials(current_user))
