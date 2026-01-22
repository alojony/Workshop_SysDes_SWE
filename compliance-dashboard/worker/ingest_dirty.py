"""
Session 3: Dirty Ingestion Pipeline
Build it dirty first - discover the hard parts

This is the "make it work" version. Participants implement this to learn:
- File discovery and registration
- Checksum-based idempotency
- Processing stage tracking
- Partial failure handling
- How messy real data is
"""
import os
import sys
import csv
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'compliance_db'),
        user=os.getenv('DB_USER', 'compliance_user'),
        password=os.getenv('DB_PASSWORD', 'compliance_pass')
    )


def hash_file(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate file checksum for idempotency

    Learning point: Idempotency - same file shouldn't be processed twice
    """
    hasher = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)

    return hasher.hexdigest()


def scan_folder(folder_path: str, extensions: List[str] = ['.csv']) -> List[Path]:
    """
    Discover files in a folder

    Learning point: File discovery and filtering
    """
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    files = []
    for ext in extensions:
        files.extend(folder.glob(f'*{ext}'))

    return sorted(files)


def register_document(conn, file_path: Path, checksum: str) -> Optional[int]:
    """
    Register document in database

    Learning point: Idempotency - check if file already exists by checksum
    Returns document_id if new or existing
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Check if document already exists
    cursor.execute(
        "SELECT id FROM documents WHERE checksum = %s",
        (checksum,)
    )

    existing = cursor.fetchone()

    if existing:
        print(f"  Document already registered: {file_path.name} (id={existing['id']})")
        cursor.close()
        return existing['id']

    # Register new document
    file_size = file_path.stat().st_size

    cursor.execute("""
        INSERT INTO documents (source, filename, file_path, checksum, file_size_bytes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (
        'CSV',
        file_path.name,
        str(file_path.absolute()),
        checksum,
        file_size
    ))

    doc_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()

    print(f"  Registered new document: {file_path.name} (id={doc_id})")
    return doc_id


def record_run(conn, document_id: int, stage: str, status: str,
               error: Optional[str] = None,
               rows_attempted: int = 0,
               rows_succeeded: int = 0,
               rows_failed: int = 0) -> int:
    """
    Record processing run in database

    Learning point: Audit trail - every processing attempt is tracked
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        INSERT INTO processing_runs
        (document_id, stage, status, error_message, rows_attempted, rows_succeeded, rows_failed, finished_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        document_id,
        stage,
        status,
        error,
        rows_attempted,
        rows_succeeded,
        rows_failed,
        datetime.now() if status in ['SUCCESS', 'FAILED', 'PARTIAL'] else None
    ))

    run_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()

    return run_id


def load_csv_inspections(conn, document_id: int, file_path: Path) -> Dict[str, int]:
    """
    Load inspection CSV into database (dirty version)

    Learning points:
    - CSV parsing can fail
    - Data might be messy
    - Partial failures should be tracked, not crash everything

    TODO for participants: Implement this function
    """
    attempted = 0
    succeeded = 0
    failed = 0
    errors = []

    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            cursor = conn.cursor()

            for row in reader:
                attempted += 1

                try:
                    # TODO: Parse CSV row
                    # TODO: Insert into inspections table
                    # TODO: Handle missing/invalid data

                    # Placeholder - participants implement this
                    succeeded += 1

                except Exception as e:
                    failed += 1
                    errors.append(f"Row {attempted}: {str(e)}")

            cursor.close()
            conn.commit()

    except Exception as e:
        return {
            'attempted': attempted,
            'succeeded': succeeded,
            'failed': failed,
            'error': str(e)
        }

    return {
        'attempted': attempted,
        'succeeded': succeeded,
        'failed': failed,
        'error': '; '.join(errors[:5]) if errors else None  # First 5 errors
    }


def load_csv_ncrs(conn, document_id: int, file_path: Path) -> Dict[str, int]:
    """
    Load NCR CSV into database (dirty version)

    TODO for participants: Implement this function
    """
    # Similar structure to load_csv_inspections
    # Participants implement this
    pass


def load_csv_maintenance(conn, document_id: int, file_path: Path) -> Dict[str, int]:
    """
    Load maintenance CSV into database (dirty version)

    TODO for participants: Implement this function
    """
    # Similar structure to load_csv_inspections
    # Participants implement this
    pass


def process_file(conn, file_path: Path):
    """
    Process a single file through the dirty pipeline

    Pipeline stages:
    1. RECEIVE - calculate checksum and register
    2. PARSE_CSV - read and parse CSV
    3. PERSIST - save to database
    """
    print(f"\nProcessing: {file_path.name}")

    # Stage 1: RECEIVE
    try:
        checksum = hash_file(file_path)
        doc_id = register_document(conn, file_path, checksum)
        record_run(conn, doc_id, 'RECEIVE', 'SUCCESS')
    except Exception as e:
        print(f"  ERROR in RECEIVE: {e}")
        return

    # Stage 2: PARSE_CSV
    try:
        # Determine file type and load accordingly
        filename = file_path.name.lower()

        if 'inspection' in filename:
            result = load_csv_inspections(conn, doc_id, file_path)
        elif 'ncr' in filename:
            result = load_csv_ncrs(conn, doc_id, file_path)
        elif 'maintenance' in filename:
            result = load_csv_maintenance(conn, doc_id, file_path)
        else:
            print(f"  Unknown file type: {filename}")
            record_run(conn, doc_id, 'PARSE_CSV', 'FAILED', error='Unknown file type')
            return

        # Record parsing result
        if result and result['attempted'] > 0:
            if result['failed'] == 0:
                status = 'SUCCESS'
            elif result['succeeded'] > 0:
                status = 'PARTIAL'
            else:
                status = 'FAILED'

            record_run(
                conn, doc_id, 'PERSIST', status,
                error=result.get('error'),
                rows_attempted=result['attempted'],
                rows_succeeded=result['succeeded'],
                rows_failed=result['failed']
            )

            print(f"  Processed {result['succeeded']}/{result['attempted']} rows")

    except Exception as e:
        print(f"  ERROR in PARSE_CSV: {e}")
        record_run(conn, doc_id, 'PARSE_CSV', 'FAILED', error=str(e))


def main():
    """
    Main ingestion function

    Learning points:
    - Idempotency: safe to run multiple times
    - Partial failures: some files can fail without breaking everything
    - Audit trail: all attempts are recorded
    """
    print("=" * 60)
    print("Dirty Ingestion Pipeline - Session 3")
    print("=" * 60)

    data_folder = os.getenv('RAW_DATA_PATH', './data/raw')

    # Scan for CSV files
    print(f"\nScanning folder: {data_folder}")
    files = scan_folder(data_folder, ['.csv'])
    print(f"Found {len(files)} CSV files")

    # Process each file
    conn = get_db_connection()

    for file_path in files:
        try:
            process_file(conn, file_path)
        except Exception as e:
            print(f"ERROR processing {file_path.name}: {e}")
            # Continue with next file - don't crash on one failure

    conn.close()

    print("\n" + "=" * 60)
    print("Ingestion complete")
    print("=" * 60)


if __name__ == '__main__':
    main()
