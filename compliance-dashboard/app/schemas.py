"""
API schemas for request/response validation
These are the contract between API and clients
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models import InspectionResult, NCRStatus, NCRSeverity, ProcessingStatus, ProcessingStage


# Health check
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str


# Failed inspections endpoint
class FailedInspectionItem(BaseModel):
    """Single failed inspection item"""
    inspection_id: str
    site: str
    supplier: Optional[str] = None
    part_number: Optional[str] = None
    part_description: Optional[str] = None
    inspection_date: date
    result: InspectionResult
    measurement_value: Optional[float] = None
    measurement_unit: Optional[str] = None
    spec_min: Optional[float] = None
    spec_max: Optional[float] = None
    document_filename: Optional[str] = None


class FailedInspectionsResponse(BaseModel):
    """Response for failed inspections query"""
    count: int
    inspections: List[FailedInspectionItem]
    filters: dict


# Open NCRs endpoint
class OpenNCRItem(BaseModel):
    """Single open NCR item"""
    ncr_id: str
    site: str
    supplier: Optional[str] = None
    part_number: Optional[str] = None
    severity: NCRSeverity
    status: NCRStatus
    description: str
    opened_at: datetime
    days_open: int
    document_filename: Optional[str] = None


class OpenNCRsResponse(BaseModel):
    """Response for open NCRs query"""
    count: int
    ncrs: List[OpenNCRItem]
    filters: dict
    severity_breakdown: dict


# Top failures endpoint
class TopFailureItem(BaseModel):
    """Single top failure item"""
    category: str
    failure_count: int
    percentage: float


class TopFailuresResponse(BaseModel):
    """Response for top failures query"""
    group_by: str
    count: int
    failures: List[TopFailureItem]
    total_failures: int


# Evidence endpoint
class EvidenceInspection(BaseModel):
    """Inspection evidence"""
    inspection_id: str
    site: str
    inspection_date: date
    result: InspectionResult
    measurement_value: Optional[float] = None
    spec_min: Optional[float] = None
    spec_max: Optional[float] = None
    document_filename: Optional[str] = None


class EvidenceDocument(BaseModel):
    """Document reference"""
    document_id: int
    filename: str
    file_path: str
    source: str
    received_at: datetime


class EvidenceResponse(BaseModel):
    """Response for evidence query"""
    ncr_id: str
    ncr_description: str
    severity: NCRSeverity
    status: NCRStatus
    opened_at: datetime
    linked_inspection: Optional[EvidenceInspection] = None
    ncr_document: Optional[EvidenceDocument] = None
    related_documents: List[EvidenceDocument] = []


# Ingestion runs endpoint
class IngestionRunItem(BaseModel):
    """Single ingestion run item"""
    run_id: int
    document_id: Optional[int] = None
    filename: Optional[str] = None
    stage: ProcessingStage
    status: ProcessingStatus
    error_message: Optional[str] = None
    rows_attempted: int
    rows_succeeded: int
    rows_failed: int
    started_at: datetime
    finished_at: Optional[datetime] = None


class IngestionRunsResponse(BaseModel):
    """Response for ingestion runs query"""
    count: int
    runs: List[IngestionRunItem]
    filters: dict


# Trend view endpoint
class TrendDataPoint(BaseModel):
    """Single trend data point"""
    period: str
    failure_count: int
    inspection_count: int
    failure_rate: float


class TrendResponse(BaseModel):
    """Response for trend query"""
    period_type: str  # 'week' or 'month'
    data_points: List[TrendDataPoint]
