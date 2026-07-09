from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import finance as crud_finance
from security import require_financial_access


router = APIRouter(
    prefix="/api/finance",
    tags=["finance"],
    dependencies=[Depends(require_financial_access)],
)


@router.get("/kpis")
def get_finance_kpis(db: Session = Depends(get_db)):
    return crud_finance.get_finance_kpis(db)
