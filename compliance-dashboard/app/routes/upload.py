"""
File Upload and Ingestion API Routes
Endpoints for uploading and processing CSV/PDF files
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from typing import List
from pathlib import Path
from datetime import datetime
import shutil
import tempfile

from app.db import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/upload", tags=["Upload & Ingestion"])


# Response models
class UploadResponse(BaseModel):
    """Response for file upload"""
    success: bool
    filename: str
    file_size: int
    file_type: str
    message: str


class IngestionResponse(BaseModel):
    """Response for ingestion operation"""
    success: bool
    document_id: int | None
    document_type: str
    rows_attempted: int
    rows_succeeded: int
    rows_failed: int
    errors: List[str] | None
    message: str


class IngestionStatusResponse(BaseModel):
    """Response for ingestion status"""
    total_documents: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    recent_runs: List[dict]


def get_file_type(filename: str) -> str:
    """Determine file type from extension"""
    ext = Path(filename).suffix.lower()
    if ext == '.csv':
        return 'csv'
    elif ext == '.pdf':
        return 'pdf'
    else:
        return 'unknown'


def process_csv_file(file_path: Path, db) -> IngestionResponse:
    """
    Process uploaded CSV file

    Args:
        file_path: Path to uploaded file
        db: Database connection

    Returns:
        IngestionResponse with results
    """
    from worker.ingest_clean import (
        load_inspections_clean,
        load_ncrs_clean,
        load_maintenance_clean
    )
    from worker.ingest_dirty import hash_file, register_document, record_run

    try:
        conn = db.get_connection()

        # Register document
        checksum = hash_file(file_path)
        doc_id = register_document(conn, file_path, checksum)

        if not doc_id:
            return IngestionResponse(
                success=False,
                document_id=None,
                document_type='csv',
                rows_attempted=0,
                rows_succeeded=0,
                rows_failed=0,
                errors=["Document already exists"],
                message="Document already processed"
            )

        # Determine file type from name
        filename = file_path.name.lower()
        if 'inspection' in filename:
            result = load_inspections_clean(conn, doc_id, file_path)
            doc_type = 'inspection_csv'
        elif 'ncr' in filename:
            result = load_ncrs_clean(conn, doc_id, file_path)
            doc_type = 'ncr_csv'
        elif 'maintenance' in filename or 'maint' in filename:
            result = load_maintenance_clean(conn, doc_id, file_path)
            doc_type = 'maintenance_csv'
        else:
            return IngestionResponse(
                success=False,
                document_id=doc_id,
                document_type='csv',
                rows_attempted=0,
                rows_succeeded=0,
                rows_failed=0,
                errors=["Unknown CSV file type - filename must contain 'inspection', 'ncr', or 'maintenance'"],
                message="Could not determine file type"
            )

        conn.close()

        # Build response
        errors = [result['error']] if result.get('error') else None

        return IngestionResponse(
            success=result['succeeded'] > 0,
            document_id=doc_id,
            document_type=doc_type,
            rows_attempted=result['attempted'],
            rows_succeeded=result['succeeded'],
            rows_failed=result['failed'],
            errors=errors,
            message=f"Processed {result['succeeded']}/{result['attempted']} rows successfully"
        )

    except Exception as e:
        return IngestionResponse(
            success=False,
            document_id=None,
            document_type='csv',
            rows_attempted=0,
            rows_succeeded=0,
            rows_failed=0,
            errors=[str(e)],
            message=f"Ingestion failed: {str(e)}"
        )


def process_pdf_file(file_path: Path, db) -> IngestionResponse:
    """
    Process uploaded PDF file

    Args:
        file_path: Path to uploaded file
        db: Database connection

    Returns:
        IngestionResponse with results
    """
    from worker.ingest_pdf import ingest_pdf_file

    try:
        conn = db.get_connection()
        result = ingest_pdf_file(file_path, conn)
        conn.close()

        if result['success']:
            return IngestionResponse(
                success=True,
                document_id=None,  # Could be enhanced to return doc_id
                document_type=result['doc_type'] or 'pdf',
                rows_attempted=1,
                rows_succeeded=1,
                rows_failed=0,
                errors=None,
                message=f"Successfully processed {result['doc_type']} PDF"
            )
        else:
            return IngestionResponse(
                success=False,
                document_id=None,
                document_type='pdf',
                rows_attempted=1,
                rows_succeeded=0,
                rows_failed=1,
                errors=[result['error']],
                message=f"PDF processing failed: {result['error']}"
            )

    except Exception as e:
        return IngestionResponse(
            success=False,
            document_id=None,
            document_type='pdf',
            rows_attempted=1,
            rows_succeeded=0,
            rows_failed=1,
            errors=[str(e)],
            message=f"PDF ingestion failed: {str(e)}"
        )


@router.post("/file", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
):
    """
    Upload a file (CSV or PDF)

    This endpoint accepts file upload but does NOT process it immediately.
    Use /upload/file/process to upload and process in one step.
    """
    try:
        # Validate file type
        file_type = get_file_type(file.filename)
        if file_type == 'unknown':
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only CSV and PDF files are allowed."
            )

        # Save to temp location
        upload_dir = Path('data/raw')
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Create unique filename to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = upload_dir / safe_filename

        # Save file
        with file_path.open('wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = file_path.stat().st_size

        return UploadResponse(
            success=True,
            filename=safe_filename,
            file_size=file_size,
            file_type=file_type,
            message=f"File uploaded successfully. Use /upload/ingest/{file_type} to process it."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/file/process", response_model=IngestionResponse)
async def upload_and_process_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db=Depends(get_db)
):
    """
    Upload and immediately process a file (CSV or PDF)

    This is the recommended endpoint for UI uploads.
    Processes the file immediately and returns ingestion results.
    """
    try:
        # Validate file type
        file_type = get_file_type(file.filename)
        if file_type == 'unknown':
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only CSV and PDF files are allowed."
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = Path(tmp_file.name)

        try:
            # Process based on type
            if file_type == 'csv':
                result = process_csv_file(tmp_path, db)
            elif file_type == 'pdf':
                result = process_pdf_file(tmp_path, db)
            else:
                raise HTTPException(status_code=400, detail="Invalid file type")

            return result

        finally:
            # Clean up temp file
            if tmp_path.exists():
                tmp_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    limit: int = 10,
    db=Depends(get_db)
):
    """
    Get ingestion pipeline status

    Shows overall statistics and recent processing runs.
    """
    try:
        with db.get_cursor() as cursor:
            # Get total documents
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            total_docs = cursor.fetchone()['count']

            # Get total runs
            cursor.execute("SELECT COUNT(*) as count FROM processing_runs")
            total_runs = cursor.fetchone()['count']

            # Get successful runs
            cursor.execute(
                "SELECT COUNT(*) as count FROM processing_runs WHERE status = 'SUCCESS'"
            )
            successful = cursor.fetchone()['count']

            # Get failed runs
            cursor.execute(
                "SELECT COUNT(*) as count FROM processing_runs WHERE status IN ('FAILED', 'PARTIAL')"
            )
            failed = cursor.fetchone()['count']

            # Get recent runs
            cursor.execute("""
                SELECT
                    pr.id,
                    pr.document_id,
                    d.filename,
                    pr.stage,
                    pr.status,
                    pr.rows_attempted,
                    pr.rows_succeeded,
                    pr.rows_failed,
                    pr.error_message,
                    pr.started_at,
                    pr.finished_at
                FROM processing_runs pr
                LEFT JOIN documents d ON pr.document_id = d.id
                ORDER BY pr.started_at DESC
                LIMIT %s
            """, (limit,))

            recent_runs = []
            for row in cursor.fetchall():
                recent_runs.append({
                    'run_id': row['id'],
                    'document_id': row['document_id'],
                    'filename': row['filename'],
                    'stage': row['stage'],
                    'status': row['status'],
                    'rows_attempted': row['rows_attempted'],
                    'rows_succeeded': row['rows_succeeded'],
                    'rows_failed': row['rows_failed'],
                    'error': row['error_message'],
                    'started_at': row['started_at'].isoformat() if row['started_at'] else None,
                    'finished_at': row['finished_at'].isoformat() if row['finished_at'] else None
                })

        return IngestionStatusResponse(
            total_documents=total_docs,
            total_runs=total_runs,
            successful_runs=successful,
            failed_runs=failed,
            recent_runs=recent_runs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/ingest/csv/{file_path:path}", response_model=IngestionResponse)
async def ingest_csv_from_path(
    file_path: str,
    db=Depends(get_db)
):
    """
    Ingest a CSV file from a server path

    Useful for processing files already on the server without uploading.

    Example: /upload/ingest/csv/data/raw/inspection_logs.csv
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if path.suffix.lower() != '.csv':
            raise HTTPException(status_code=400, detail="File must be a CSV")

        result = process_csv_file(path, db)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/pdf/{file_path:path}", response_model=IngestionResponse)
async def ingest_pdf_from_path(
    file_path: str,
    db=Depends(get_db)
):
    """
    Ingest a PDF file from a server path

    Example: /upload/ingest/pdf/data/raw/pdf/ncr/NCR-2024-001.pdf
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if path.suffix.lower() != '.pdf':
            raise HTTPException(status_code=400, detail="File must be a PDF")

        result = process_pdf_file(path, db)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
