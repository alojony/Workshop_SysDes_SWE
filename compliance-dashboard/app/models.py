"""
Pydantic models for database entities
These represent the database tables as Python objects
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from enum import Enum


# Enums matching database types
class DocumentSource(str, Enum):
    CSV = "CSV"
    PDF = "PDF"
    API = "API"
    MANUAL = "MANUAL"


class ProcessingStage(str, Enum):
    RECEIVE = "RECEIVE"
    PARSE_CSV = "PARSE_CSV"
    NORMALIZE = "NORMALIZE"
    VALIDATE = "VALIDATE"
    PERSIST = "PERSIST"


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class InspectionResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CONDITIONAL = "CONDITIONAL"


class NCRStatus(str, Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class NCRSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Database Models
class Document(BaseModel):
    """Document model"""
    id: Optional[int] = None
    source: DocumentSource
    filename: str
    file_path: str
    checksum: str
    file_size_bytes: Optional[int] = None
    received_at: datetime = datetime.now()
    metadata: Optional[dict] = None


class ProcessingRun(BaseModel):
    """Processing run model"""
    id: Optional[int] = None
    document_id: Optional[int] = None
    stage: ProcessingStage
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    rows_attempted: int = 0
    rows_succeeded: int = 0
    rows_failed: int = 0
    started_at: datetime = datetime.now()
    finished_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class Inspection(BaseModel):
    """Inspection model"""
    id: Optional[int] = None
    inspection_id: str
    document_id: Optional[int] = None
    site: str
    production_line: Optional[str] = None
    supplier: Optional[str] = None
    part_number: Optional[str] = None
    part_description: Optional[str] = None
    inspection_date: date
    inspector: Optional[str] = None
    result: InspectionResult
    measurement_value: Optional[float] = None
    measurement_unit: Optional[str] = None
    spec_min: Optional[float] = None
    spec_max: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class NCR(BaseModel):
    """Non-conformance report model"""
    id: Optional[int] = None
    ncr_id: str
    document_id: Optional[int] = None
    linked_inspection_id: Optional[int] = None
    site: str
    supplier: Optional[str] = None
    part_number: Optional[str] = None
    part_description: Optional[str] = None
    severity: NCRSeverity
    status: NCRStatus = NCRStatus.OPEN
    description: str
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    opened_at: datetime
    reviewed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    days_open: Optional[int] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class MaintenanceEvent(BaseModel):
    """Maintenance event model"""
    id: Optional[int] = None
    event_id: str
    document_id: Optional[int] = None
    site: str
    machine_id: str
    machine_description: Optional[str] = None
    event_type: Optional[str] = None
    event_date: date
    downtime_hours: Optional[float] = None
    technician: Optional[str] = None
    description: Optional[str] = None
    parts_replaced: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
