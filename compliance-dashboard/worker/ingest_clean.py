"""
Session 4: Clean Ingestion Pipeline
Engineering it properly with normalization and validation

This is the "make it right" version after learning from dirty implementation
"""
import os
import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Import normalization functions
from worker.normalize import (
    normalize_date,
    normalize_datetime,
    normalize_decimal,
    normalize_status,
    normalize_unit,
    clean_string,
    validate_row,
    normalize_inspection_row
)

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


def load_inspections_clean(conn, document_id: int, file_path: Path) -> Dict:
    """
    Load inspections with full normalization and validation

    Learning points:
    - Transaction boundaries
    - Row-level error capture
    - Normalization pipeline
    - Validation before insert
    """
    attempted = 0
    succeeded = 0
    failed = 0
    errors = []

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                attempted += 1

                try:
                    # Validate required fields
                    validation_errors = validate_row(
                        row,
                        required_fields=['inspection_id', 'site', 'inspection_date', 'result'],
                        row_num=row_num
                    )

                    if validation_errors:
                        raise ValueError('; '.join(validation_errors))

                    # Normalize the row
                    normalized = normalize_inspection_row(row)

                    # Check for duplicate inspection_id
                    cursor.execute(
                        "SELECT id FROM inspections WHERE inspection_id = %s",
                        (normalized['inspection_id'],)
                    )

                    if cursor.fetchone():
                        # Already exists - skip (idempotency)
                        succeeded += 1
                        continue

                    # Insert normalized data
                    cursor.execute("""
                        INSERT INTO inspections
                        (inspection_id, document_id, site, production_line, supplier,
                         part_number, part_description, inspection_date, inspector, result,
                         measurement_value, measurement_unit, spec_min, spec_max, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        normalized['inspection_id'],
                        document_id,
                        normalized['site'],
                        normalized['production_line'],
                        normalized['supplier'],
                        normalized['part_number'],
                        normalized['part_description'],
                        normalized['inspection_date'],
                        normalized['inspector'],
                        normalized['result'],
                        normalized['measurement_value'],
                        normalized['measurement_unit'],
                        normalized['spec_min'],
                        normalized['spec_max'],
                        normalized['notes']
                    ))

                    succeeded += 1

                except Exception as e:
                    failed += 1
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    print(f"  WARNING: {error_msg}")
                    # Continue processing other rows

        conn.commit()

    except Exception as e:
        conn.rollback()
        return {
            'attempted': attempted,
            'succeeded': succeeded,
            'failed': failed,
            'error': f"Fatal error: {str(e)}"
        }
    finally:
        cursor.close()

    return {
        'attempted': attempted,
        'succeeded': succeeded,
        'failed': failed,
        'error': '; '.join(errors[:10]) if errors else None  # First 10 errors
    }


def load_ncrs_clean(conn, document_id: int, file_path: Path) -> Dict:
    """
    Load NCRs with full normalization and validation

    TODO for participants: Implement similar to load_inspections_clean

    Special considerations:
    - linked_inspection_id might reference inspection that doesn't exist yet
    - dates: opened_at, reviewed_at, closed_at
    - severity and status enums
    """
    attempted = 0
    succeeded = 0
    failed = 0
    errors = []

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):
                attempted += 1

                try:
                    # Validate
                    validation_errors = validate_row(
                        row,
                        required_fields=['ncr_id', 'site', 'severity', 'status', 'description', 'opened_at'],
                        row_num=row_num
                    )

                    if validation_errors:
                        raise ValueError('; '.join(validation_errors))

                    # Normalize
                    ncr_id = clean_string(row.get('ncr_id'), 100)
                    site = clean_string(row.get('site'), 100)
                    supplier = clean_string(row.get('supplier'), 200)
                    part_number = clean_string(row.get('part_number'), 100)
                    part_description = clean_string(row.get('part_description'))
                    severity = normalize_status(row.get('severity'), 'ncr_severity')
                    status = normalize_status(row.get('status'), 'ncr_status')
                    description = clean_string(row.get('description'))
                    root_cause = clean_string(row.get('root_cause'))
                    corrective_action = clean_string(row.get('corrective_action'))
                    opened_at = normalize_datetime(row.get('opened_at'))
                    reviewed_at = normalize_datetime(row.get('reviewed_at'))
                    closed_at = normalize_datetime(row.get('closed_at'))

                    # Handle linked inspection
                    linked_inspection_id = None
                    linked_inspection_ref = clean_string(row.get('linked_inspection_id'))

                    if linked_inspection_ref:
                        cursor.execute(
                            "SELECT id FROM inspections WHERE inspection_id = %s",
                            (linked_inspection_ref,)
                        )
                        inspection = cursor.fetchone()
                        if inspection:
                            linked_inspection_id = inspection['id']

                    # Check for duplicate
                    cursor.execute(
                        "SELECT id FROM ncrs WHERE ncr_id = %s",
                        (ncr_id,)
                    )

                    if cursor.fetchone():
                        succeeded += 1
                        continue

                    # Insert
                    cursor.execute("""
                        INSERT INTO ncrs
                        (ncr_id, document_id, linked_inspection_id, site, supplier,
                         part_number, part_description, severity, status, description,
                         root_cause, corrective_action, opened_at, reviewed_at, closed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ncr_id, document_id, linked_inspection_id, site, supplier,
                        part_number, part_description, severity, status, description,
                        root_cause, corrective_action, opened_at, reviewed_at, closed_at
                    ))

                    succeeded += 1

                except Exception as e:
                    failed += 1
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    print(f"  WARNING: {error_msg}")

        conn.commit()

    except Exception as e:
        conn.rollback()
        return {
            'attempted': attempted,
            'succeeded': succeeded,
            'failed': failed,
            'error': f"Fatal error: {str(e)}"
        }
    finally:
        cursor.close()

    return {
        'attempted': attempted,
        'succeeded': succeeded,
        'failed': failed,
        'error': '; '.join(errors[:10]) if errors else None
    }


def load_maintenance_clean(conn, document_id: int, file_path: Path) -> Dict:
    """
    Load maintenance events with normalization

    TODO for participants: Implement
    """
    attempted = 0
    succeeded = 0
    failed = 0

    # Participants implement this
    # Similar pattern to inspections and NCRs

    return {
        'attempted': attempted,
        'succeeded': succeeded,
        'failed': failed,
        'error': None
    }


def main():
    """
    Main clean ingestion pipeline

    Improvements over dirty version:
    - Full normalization
    - Better error handling
    - Row-level error tracking
    - Transaction boundaries
    - Validation before persistence
    """
    print("=" * 60)
    print("Clean Ingestion Pipeline - Session 4")
    print("=" * 60)

    from worker.ingest_dirty import scan_folder, hash_file, register_document, record_run

    data_folder = os.getenv('RAW_DATA_PATH', './data/raw')

    print(f"\nScanning folder: {data_folder}")
    files = scan_folder(data_folder, ['.csv'])
    print(f"Found {len(files)} CSV files\n")

    conn = get_db_connection()

    for file_path in files:
        print(f"Processing: {file_path.name}")

        try:
            # Register document
            checksum = hash_file(file_path)
            doc_id = register_document(conn, file_path, checksum)
            record_run(conn, doc_id, 'RECEIVE', 'SUCCESS')

            # Determine file type and process
            filename = file_path.name.lower()

            if 'inspection' in filename:
                result = load_inspections_clean(conn, doc_id, file_path)
            elif 'ncr' in filename:
                result = load_ncrs_clean(conn, doc_id, file_path)
            elif 'maintenance' in filename:
                result = load_maintenance_clean(conn, doc_id, file_path)
            else:
                print(f"  Unknown file type")
                continue

            # Record result
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

            print(f"  ✓ Success: {result['succeeded']}/{result['attempted']} rows")
            if result['failed'] > 0:
                print(f"  ✗ Failed: {result['failed']} rows")

        except Exception as e:
            print(f"  ERROR: {e}")

    conn.close()

    print("\n" + "=" * 60)
    print("Clean ingestion complete")
    print("=" * 60)


if __name__ == '__main__':
    main()
