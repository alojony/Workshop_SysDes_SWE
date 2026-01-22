"""
Operational API routes
For monitoring ingestion pipeline health
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from datetime import date
from app.schemas import IngestionRunsResponse
from app.db import get_db

router = APIRouter(prefix="/ops", tags=["Operations"])


@router.get("/ingestion-runs", response_model=IngestionRunsResponse)
async def get_ingestion_runs(
    status: Optional[str] = None,
    stage: Optional[str] = None,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_db)
):
    """
    Get ingestion pipeline runs with filtering

    Question 5: Ingestion health: what failed processing and why (by stage)
    """
    # TODO: Implement in Session 5
    return IngestionRunsResponse(
        count=0,
        runs=[],
        filters={
            "status": status,
            "stage": stage,
            "from": from_date,
            "to": to_date,
            "limit": limit
        }
    )
