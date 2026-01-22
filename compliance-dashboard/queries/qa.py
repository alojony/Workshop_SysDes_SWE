"""
Q&A Query Functions
Session 5: Python functions to execute the canonical queries

These functions are used by the FastAPI endpoints
"""
from datetime import date, datetime
from typing import Optional, List, Dict
from psycopg2.extras import RealDictCursor


def get_failed_inspections(
    cursor,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    site: Optional[str] = None,
    supplier: Optional[str] = None,
    part: Optional[str] = None
) -> List[Dict]:
    """
    Question 1: Get failed inspections with filters

    Returns list of failed inspection records with evidence
    """
    query = """
        SELECT
            i.inspection_id,
            i.site,
            i.production_line,
            i.supplier,
            i.part_number,
            i.part_description,
            i.inspection_date,
            i.result,
            i.measurement_value,
            i.measurement_unit,
            i.spec_min,
            i.spec_max,
            i.notes,
            d.filename as document_filename
        FROM inspections i
        LEFT JOIN documents d ON i.document_id = d.id
        WHERE i.result = 'FAIL'
          AND (%(from_date)s IS NULL OR i.inspection_date >= %(from_date)s)
          AND (%(to_date)s IS NULL OR i.inspection_date <= %(to_date)s)
          AND (%(site)s IS NULL OR i.site = %(site)s)
          AND (%(supplier)s IS NULL OR i.supplier = %(supplier)s)
          AND (%(part)s IS NULL OR i.part_number = %(part)s)
        ORDER BY i.inspection_date DESC
    """

    cursor.execute(query, {
        'from_date': from_date,
        'to_date': to_date,
        'site': site,
        'supplier': supplier,
        'part': part
    })

    return cursor.fetchall()


def get_open_ncrs(
    cursor,
    older_than_days: Optional[int] = None,
    severity: Optional[str] = None
) -> Dict:
    """
    Question 2: Get open NCRs beyond SLA with severity breakdown

    Returns dict with:
    - ncrs: list of NCR records
    - severity_breakdown: dict of severity -> count
    """
    # Main query
    query = """
        SELECT
            n.ncr_id,
            n.site,
            n.supplier,
            n.part_number,
            n.part_description,
            n.severity,
            n.status,
            n.description,
            n.opened_at,
            n.days_open,
            d.filename as document_filename
        FROM ncrs n
        LEFT JOIN documents d ON n.document_id = d.id
        WHERE n.status IN ('OPEN', 'IN_REVIEW')
          AND (%(older_than_days)s IS NULL OR n.days_open > %(older_than_days)s)
          AND (%(severity)s IS NULL OR n.severity = %(severity)s)
        ORDER BY n.days_open DESC, n.severity DESC
    """

    cursor.execute(query, {
        'older_than_days': older_than_days,
        'severity': severity
    })

    ncrs = cursor.fetchall()

    # Severity breakdown query
    breakdown_query = """
        SELECT
            n.severity,
            COUNT(*) as count
        FROM ncrs n
        WHERE n.status IN ('OPEN', 'IN_REVIEW')
          AND (%(older_than_days)s IS NULL OR n.days_open > %(older_than_days)s)
        GROUP BY n.severity
        ORDER BY
            CASE n.severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
            END
    """

    cursor.execute(breakdown_query, {
        'older_than_days': older_than_days
    })

    breakdown = {row['severity']: row['count'] for row in cursor.fetchall()}

    return {
        'ncrs': ncrs,
        'severity_breakdown': breakdown
    }


def get_top_failures(
    cursor,
    group_by: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Question 3: Get top failure sources

    group_by: 'supplier', 'machine', or 'part'
    Returns list of failure sources with counts
    """
    if group_by == 'supplier':
        query = """
            SELECT
                i.supplier as category,
                COUNT(*) as failure_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM inspections i
            WHERE i.result = 'FAIL'
              AND (%(from_date)s IS NULL OR i.inspection_date >= %(from_date)s)
              AND (%(to_date)s IS NULL OR i.inspection_date <= %(to_date)s)
              AND i.supplier IS NOT NULL
            GROUP BY i.supplier
            ORDER BY failure_count DESC
            LIMIT %(limit)s
        """

    elif group_by == 'part':
        query = """
            SELECT
                i.part_number || ' - ' || COALESCE(i.part_description, '') as category,
                COUNT(*) as failure_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM inspections i
            WHERE i.result = 'FAIL'
              AND (%(from_date)s IS NULL OR i.inspection_date >= %(from_date)s)
              AND (%(to_date)s IS NULL OR i.inspection_date <= %(to_date)s)
              AND i.part_number IS NOT NULL
            GROUP BY i.part_number, i.part_description
            ORDER BY failure_count DESC
            LIMIT %(limit)s
        """

    elif group_by == 'machine':
        query = """
            SELECT
                m.machine_id || ' - ' || COALESCE(m.machine_description, '') as category,
                COUNT(DISTINCT m.event_id) as failure_count,
                0.0 as percentage
            FROM maintenance_events m
            WHERE m.event_type IN ('Breakdown', 'Corrective')
              AND (%(from_date)s IS NULL OR m.event_date >= %(from_date)s)
              AND (%(to_date)s IS NULL OR m.event_date <= %(to_date)s)
            GROUP BY m.machine_id, m.machine_description
            ORDER BY failure_count DESC
            LIMIT %(limit)s
        """

    else:
        raise ValueError(f"Invalid group_by: {group_by}")

    cursor.execute(query, {
        'from_date': from_date,
        'to_date': to_date,
        'limit': limit
    })

    results = cursor.fetchall()

    # Calculate percentages for machine if needed
    if group_by == 'machine' and results:
        total = sum(r['failure_count'] for r in results)
        for r in results:
            r['percentage'] = round(r['failure_count'] * 100.0 / total, 2) if total > 0 else 0.0

    return results


def get_evidence(cursor, ncr_id: str) -> Optional[Dict]:
    """
    Question 4: Get evidence chain for an NCR

    Returns dict with:
    - ncr: NCR details
    - linked_inspection: inspection details (if any)
    - ncr_document: document that contains the NCR
    - related_documents: list of related documents
    """
    query = """
        SELECT
            n.ncr_id,
            n.description as ncr_description,
            n.severity,
            n.status,
            n.opened_at,
            n.reviewed_at,
            n.closed_at,
            n.days_open,
            -- Linked inspection
            i.inspection_id,
            i.site as inspection_site,
            i.inspection_date,
            i.result,
            i.measurement_value,
            i.measurement_unit,
            i.spec_min,
            i.spec_max,
            -- NCR document
            d_ncr.id as ncr_document_id,
            d_ncr.filename as ncr_document_filename,
            d_ncr.file_path as ncr_document_path,
            d_ncr.source as ncr_document_source,
            d_ncr.received_at as ncr_document_received,
            -- Inspection document
            d_inspection.id as inspection_document_id,
            d_inspection.filename as inspection_document_filename,
            d_inspection.file_path as inspection_document_path,
            d_inspection.source as inspection_document_source,
            d_inspection.received_at as inspection_document_received
        FROM ncrs n
        LEFT JOIN inspections i ON n.linked_inspection_id = i.id
        LEFT JOIN documents d_ncr ON n.document_id = d_ncr.id
        LEFT JOIN documents d_inspection ON i.document_id = d_inspection.id
        WHERE n.ncr_id = %(ncr_id)s
    """

    cursor.execute(query, {'ncr_id': ncr_id})
    result = cursor.fetchone()

    if not result:
        return None

    # Structure the response
    evidence = {
        'ncr_id': result['ncr_id'],
        'ncr_description': result['ncr_description'],
        'severity': result['severity'],
        'status': result['status'],
        'opened_at': result['opened_at'],
        'reviewed_at': result['reviewed_at'],
        'closed_at': result['closed_at'],
        'days_open': result['days_open'],
    }

    # Add linked inspection if exists
    if result['inspection_id']:
        evidence['linked_inspection'] = {
            'inspection_id': result['inspection_id'],
            'site': result['inspection_site'],
            'inspection_date': result['inspection_date'],
            'result': result['result'],
            'measurement_value': result['measurement_value'],
            'measurement_unit': result['measurement_unit'],
            'spec_min': result['spec_min'],
            'spec_max': result['spec_max'],
            'document_filename': result['inspection_document_filename']
        }

    # Add NCR document if exists
    if result['ncr_document_id']:
        evidence['ncr_document'] = {
            'document_id': result['ncr_document_id'],
            'filename': result['ncr_document_filename'],
            'file_path': result['ncr_document_path'],
            'source': result['ncr_document_source'],
            'received_at': result['ncr_document_received']
        }

    return evidence


def get_ingestion_runs(
    cursor,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Question 5: Get ingestion pipeline runs (health monitoring)

    Returns list of processing runs with details
    """
    query = """
        SELECT
            pr.id as run_id,
            pr.document_id,
            d.filename,
            pr.stage,
            pr.status,
            pr.error_message,
            pr.rows_attempted,
            pr.rows_succeeded,
            pr.rows_failed,
            pr.started_at,
            pr.finished_at
        FROM processing_runs pr
        LEFT JOIN documents d ON pr.document_id = d.id
        WHERE (%(status)s IS NULL OR pr.status = %(status)s)
          AND (%(stage)s IS NULL OR pr.stage = %(stage)s)
          AND (%(from_date)s IS NULL OR DATE(pr.started_at) >= %(from_date)s)
          AND (%(to_date)s IS NULL OR DATE(pr.started_at) <= %(to_date)s)
        ORDER BY pr.started_at DESC
        LIMIT %(limit)s
    """

    cursor.execute(query, {
        'status': status,
        'stage': stage,
        'from_date': from_date,
        'to_date': to_date,
        'limit': limit
    })

    return cursor.fetchall()


def get_trends(
    cursor,
    period: str = 'week',
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict]:
    """
    Question 6: Get failure trends over time

    period: 'week' or 'month'
    Returns list of time periods with failure statistics
    """
    if period == 'week':
        trunc_func = "DATE_TRUNC('week', i.inspection_date)"
        default_interval = "12 weeks"
    elif period == 'month':
        trunc_func = "DATE_TRUNC('month', i.inspection_date)"
        default_interval = "12 months"
    else:
        raise ValueError(f"Invalid period: {period}")

    query = f"""
        SELECT
            {trunc_func} as period_start,
            COUNT(*) FILTER (WHERE i.result = 'FAIL') as failure_count,
            COUNT(*) as inspection_count,
            ROUND(
                COUNT(*) FILTER (WHERE i.result = 'FAIL') * 100.0 / NULLIF(COUNT(*), 0),
                2
            ) as failure_rate
        FROM inspections i
        WHERE (%(from_date)s IS NULL OR i.inspection_date >= %(from_date)s)
          AND (%(to_date)s IS NULL OR i.inspection_date <= %(to_date)s)
        GROUP BY {trunc_func}
        ORDER BY period_start DESC
    """

    cursor.execute(query, {
        'from_date': from_date or f"NOW() - INTERVAL '{default_interval}'",
        'to_date': to_date
    })

    return cursor.fetchall()
