from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ....core.database import get_db

router = APIRouter()

@router.get("/ml-opportunities/test")
async def test_ml_opportunities(db: Session = Depends(get_db)):
    """Simple test endpoint for ML opportunities."""
    try:
        result = db.execute(text("SELECT COUNT(*) as count FROM ml_opportunities"))
        count = result.fetchone().count
        return {"count": count, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}
