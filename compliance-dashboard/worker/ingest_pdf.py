"""
PDF Ingestion Module
Extracts data from PDF documents and ingests into database

Supports:
- NCR Report PDFs
- Inspection Certificate PDFs
- Maintenance Work Order PDFs
"""
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("Warning: pdfplumber not installed. Install with: pip install pdfplumber")

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


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract all text from a PDF file

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text as string
    """
    if not PDF_SUPPORT:
        raise ImportError("PDF support not available. Install pdfplumber.")

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


def extract_field(text: str, pattern: str, default: Optional[str] = None) -> Optional[str]:
    """
    Extract a field from text using regex pattern

    Args:
        text: Text to search
        pattern: Regex pattern
        default: Default value if not found

    Returns:
        Extracted value or default
    """
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return default


def parse_ncr_pdf(pdf_path: Path, text: str) -> Optional[Dict]:
    """
    Parse NCR Report PDF and extract fields

    Args:
        pdf_path: Path to PDF
        text: Extracted text from PDF

    Returns:
        Dictionary with NCR data or None
    """
    # Extract NCR ID from filename or text
    ncr_id = pdf_path.stem  # e.g., NCR-2024-001

    # Extract fields using patterns
    data = {
        'ncr_id': ncr_id,
        'title': extract_field(text, r'Title:\s*(.+?)(?:\n|$)'),
        'site': extract_field(text, r'(?:Site|Location):\s*(.+?)(?:\n|$)'),
        'supplier': extract_field(text, r'Supplier:\s*(.+?)(?:\n|$)'),
        'part_number': extract_field(text, r'Part Number:\s*(.+?)(?:\n|$)'),
        'severity': extract_field(text, r'Severity:\s*(.+?)(?:\n|$)', 'MEDIUM'),
        'status': extract_field(text, r'Status:\s*(.+?)(?:\n|$)', 'OPEN'),
        'description': extract_field(text, r'Description:\s*(.+?)(?:\n|Initial)', ''),
        'opened_at': datetime.now(),  # Could parse from PDF date
    }

    # Validate minimum required fields
    if not data.get('ncr_id'):
        return None

    return data


def parse_inspection_pdf(pdf_path: Path, text: str) -> Optional[Dict]:
    """
    Parse Inspection Certificate PDF and extract fields

    Args:
        pdf_path: Path to PDF
        text: Extracted text from PDF

    Returns:
        Dictionary with inspection data or None
    """
    # Extract Inspection ID from filename or text
    inspection_id = pdf_path.stem  # e.g., INS-2024-001

    # Extract fields
    data = {
        'inspection_id': inspection_id,
        'site': extract_field(text, r'Site(?: Location)?:\s*(.+?)(?:\n|$)'),
        'part_number': extract_field(text, r'Part Number:\s*(.+?)(?:\n|$)'),
        'part_description': extract_field(text, r'Description:\s*(.+?)(?:\n|$)'),
        'supplier': extract_field(text, r'Supplier:\s*(.+?)(?:\n|$)'),
        'inspector': extract_field(text, r'Inspector:\s*(.+?)(?:\n|$)'),
        'inspection_date': extract_field(text, r'Inspection Date:\s*(.+?)(?:\n|$)'),
        'result': extract_field(text, r'(?:INSPECTION )?RESULT:\s*(.+?)(?:\n|$)', 'FAIL'),
    }

    # Try to extract measurement data
    measured = extract_field(text, r'(?:Measured Value|Dimension).*?(\d+\.?\d*)')
    if measured:
        data['measurement_value'] = float(measured)

    spec_min = extract_field(text, r'Spec Min.*?(\d+\.?\d*)')
    if spec_min:
        data['spec_min'] = float(spec_min)

    spec_max = extract_field(text, r'Spec Max.*?(\d+\.?\d*)')
    if spec_max:
        data['spec_max'] = float(spec_max)

    if not data.get('inspection_id'):
        return None

    return data


def parse_maintenance_pdf(pdf_path: Path, text: str) -> Optional[Dict]:
    """
    Parse Maintenance Work Order PDF and extract fields

    Args:
        pdf_path: Path to PDF
        text: Extracted text from PDF

    Returns:
        Dictionary with maintenance data or None
    """
    # Extract event ID from filename or text
    event_id = pdf_path.stem  # e.g., MNT-2024-001

    # Extract fields
    data = {
        'event_id': event_id,
        'site': extract_field(text, r'Site:\s*(.+?)(?:\n|$)'),
        'machine_id': extract_field(text, r'Machine ID:\s*(.+?)(?:\n|$)'),
        'machine_description': extract_field(text, r'Description:\s*(.+?)(?:\n|(?:Location|Work))'),
        'event_type': extract_field(text, r'Type:\s*(.+?)(?:\n|$)', 'Preventive'),
        'event_date': extract_field(text, r'Event Date:\s*(.+?)(?:\n|$)'),
        'technician': extract_field(text, r'Technician:\s*(.+?)(?:\n|$)'),
        'downtime_hours': extract_field(text, r'Downtime.*?(\d+\.?\d*)'),
        'description': extract_field(text, r'WORK DESCRIPTION\s+(.+?)(?:\n\n|PARTS)', ''),
    }

    if not data.get('event_id'):
        return None

    return data


def determine_pdf_type(pdf_path: Path, text: str) -> Optional[str]:
    """
    Determine the type of PDF document

    Args:
        pdf_path: Path to PDF
        text: Extracted text

    Returns:
        'ncr', 'inspection', 'maintenance', or None
    """
    filename = pdf_path.name.lower()
    text_upper = text.upper()

    # Check filename patterns
    if filename.startswith('ncr'):
        return 'ncr'
    elif filename.startswith('ins'):
        return 'inspection'
    elif filename.startswith('mnt'):
        return 'maintenance'

    # Check content patterns
    if 'NON-CONFORMANCE' in text_upper or 'NCR' in text_upper[:500]:
        return 'ncr'
    elif 'INSPECTION CERTIFICATE' in text_upper:
        return 'inspection'
    elif 'MAINTENANCE WORK ORDER' in text_upper or 'WORK ORDER' in text_upper:
        return 'maintenance'

    return None


def ingest_pdf_file(pdf_path: Path, conn) -> Dict:
    """
    Ingest a single PDF file

    Args:
        pdf_path: Path to PDF file
        conn: Database connection

    Returns:
        Result dictionary with status
    """
    from worker.ingest_dirty import hash_file, register_document, record_run

    result = {
        'success': False,
        'doc_type': None,
        'error': None
    }

    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)

        if not text or len(text) < 50:
            result['error'] = "Insufficient text extracted from PDF"
            return result

        # Determine document type
        doc_type = determine_pdf_type(pdf_path, text)
        result['doc_type'] = doc_type

        if not doc_type:
            result['error'] = "Could not determine PDF document type"
            return result

        # Register document
        checksum = hash_file(pdf_path)
        doc_id = register_document(conn, pdf_path, checksum)

        if not doc_id:
            result['error'] = "Failed to register document"
            return result

        record_run(conn, doc_id, 'RECEIVE', 'SUCCESS')

        # Parse based on type
        if doc_type == 'ncr':
            data = parse_ncr_pdf(pdf_path, text)
            if data:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ncrs
                    (ncr_id, document_id, site, supplier, part_number,
                     severity, status, description, opened_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ncr_id) DO NOTHING
                """, (
                    data['ncr_id'], doc_id, data.get('site'), data.get('supplier'),
                    data.get('part_number'), data['severity'], data['status'],
                    data.get('description'), data['opened_at']
                ))
                cursor.close()
                conn.commit()

        elif doc_type == 'inspection':
            data = parse_inspection_pdf(pdf_path, text)
            if data:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO inspections
                    (inspection_id, document_id, site, part_number, part_description,
                     supplier, inspector, inspection_date, result,
                     measurement_value, spec_min, spec_max)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (inspection_id) DO NOTHING
                """, (
                    data['inspection_id'], doc_id, data.get('site'),
                    data.get('part_number'), data.get('part_description'),
                    data.get('supplier'), data.get('inspector'),
                    data.get('inspection_date'), data['result'],
                    data.get('measurement_value'), data.get('spec_min'),
                    data.get('spec_max')
                ))
                cursor.close()
                conn.commit()

        elif doc_type == 'maintenance':
            data = parse_maintenance_pdf(pdf_path, text)
            if data:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO maintenance_events
                    (event_id, document_id, site, machine_id, machine_description,
                     event_type, event_date, technician, downtime_hours, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                """, (
                    data['event_id'], doc_id, data.get('site'),
                    data.get('machine_id'), data.get('machine_description'),
                    data['event_type'], data.get('event_date'),
                    data.get('technician'), data.get('downtime_hours'),
                    data.get('description')
                ))
                cursor.close()
                conn.commit()

        record_run(conn, doc_id, 'PERSIST', 'SUCCESS', rows_attempted=1, rows_succeeded=1)
        result['success'] = True

    except Exception as e:
        result['error'] = str(e)
        print(f"ERROR processing {pdf_path.name}: {e}")

    return result


def main():
    """Process all PDF files in data/raw/pdf/"""
    print("=" * 60)
    print("PDF Ingestion Pipeline")
    print("=" * 60)

    if not PDF_SUPPORT:
        print("ERROR: PDF support not available. Install pdfplumber:")
        print("  pip install pdfplumber")
        sys.exit(1)

    pdf_folders = [
        Path('data/raw/pdf/ncr'),
        Path('data/raw/pdf/inspections'),
        Path('data/raw/pdf/maintenance')
    ]

    conn = get_db_connection()

    total_processed = 0
    total_success = 0
    total_failed = 0

    for folder in pdf_folders:
        if not folder.exists():
            continue

        pdf_files = list(folder.glob('*.pdf'))
        if not pdf_files:
            continue

        print(f"\nProcessing {folder}: {len(pdf_files)} PDFs")

        for pdf_file in pdf_files:
            result = ingest_pdf_file(pdf_file, conn)
            total_processed += 1

            if result['success']:
                total_success += 1
                print(f"  ✓ {pdf_file.name} ({result['doc_type']})")
            else:
                total_failed += 1
                print(f"  ✗ {pdf_file.name}: {result['error']}")

    conn.close()

    print("\n" + "=" * 60)
    print(f"Processed {total_processed} PDFs")
    print(f"  Success: {total_success}")
    print(f"  Failed: {total_failed}")
    print("=" * 60)


if __name__ == '__main__':
    main()
