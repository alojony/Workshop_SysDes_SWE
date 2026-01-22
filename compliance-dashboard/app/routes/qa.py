"""
Q&A API routes
Session 5: Implement the canonical Q&A endpoints
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from datetime import date
from app.schemas import (
    FailedInspectionsResponse,
    OpenNCRsResponse,
    TopFailuresResponse,
    EvidenceResponse,
    TrendResponse
)
from app.db import get_db

router = APIRouter(prefix="/qa", tags=["Q&A"])


@router.get("/failed-inspections", response_model=FailedInspectionsResponse)
async def get_failed_inspections(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    site: Optional[str] = None,
    supplier: Optional[str] = None,
    part: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Get failed inspections in a date range with optional filters

    Question 1: Failed inspections in a date range (filters: site/line/supplier/part)
    """
    # TODO: Implement in Session 5
    # This is a stub for the workshop participants to implement
    return FailedInspectionsResponse(
        count=0,
        inspections=[],
        filters={
            "from": from_date,
            "to": to_date,
            "site": site,
            "supplier": supplier,
            "part": part
        }
    )


@router.get("/open-ncrs", response_model=OpenNCRsResponse)
async def get_open_ncrs(
    older_than_days: Optional[int] = Query(None),
    severity: Optional[str] = None,
    db=Depends(get_db)
):
    """
    Get open NCRs beyond SLA with severity breakdown

    Question 2: NCRs open beyond SLA (e.g., > 30 days) + severity breakdown
    """
    # TODO: Implement in Session 5
    return OpenNCRsResponse(
        count=0,
        ncrs=[],
        filters={
            "older_than_days": older_than_days,
            "severity": severity
        },
        severity_breakdown={}
    )


@router.get("/top-failures", response_model=TopFailuresResponse)
async def get_top_failures(
    group_by: str = Query(..., regex="^(supplier|machine|part)$"),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db)
):
    """
    Get top failure sources grouped by supplier, machine, or part

    Question 3: Top failure sources (supplier, machine, part)
    """
    # TODO: Implement in Session 5
    return TopFailuresResponse(
        group_by=group_by,
        count=0,
        failures=[],
        total_failures=0
    )


@router.get("/evidence", response_model=EvidenceResponse)
async def get_evidence(
    ncr_id: str = Query(...),
    db=Depends(get_db)
):
    """
    Get evidence chain for an NCR: linked inspection + raw documents

    Question 4: Evidence view: given NCR, show linked inspection + raw document references
    """
    # TODO: Implement in Session 5
    raise HTTPException(status_code=404, detail="NCR not found or not implemented yet")


@router.get("/trends", response_model=TrendResponse)
async def get_trends(
    period: str = Query("week", regex="^(week|month)$"),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db=Depends(get_db)
):
    """
    Get failure trends over time (weekly or monthly)

    Question 6: Trend view: failures per week/month
    """
    # TODO: Implement in Session 5
    return TrendResponse(
        period_type=period,
        data_points=[]
    )
