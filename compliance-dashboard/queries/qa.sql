-- Compliance Dashboard Q&A Queries
-- Session 5: Reference SQL for the canonical questions

-- =============================================================================
-- Question 1: Failed inspections in a date range (filters: site/line/supplier/part)
-- =============================================================================

-- Basic query
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
    d.filename as document_filename
FROM inspections i
LEFT JOIN documents d ON i.document_id = d.id
WHERE i.result = 'FAIL'
  AND i.inspection_date >= '2024-01-01'
  AND i.inspection_date <= '2024-12-31'
ORDER BY i.inspection_date DESC;

-- With optional filters (use NULL to skip filter)
SELECT
    i.inspection_id,
    i.site,
    i.supplier,
    i.part_number,
    i.inspection_date,
    i.result,
    d.filename
FROM inspections i
LEFT JOIN documents d ON i.document_id = d.id
WHERE i.result = 'FAIL'
  AND i.inspection_date BETWEEN $1 AND $2
  AND ($3 IS NULL OR i.site = $3)
  AND ($4 IS NULL OR i.supplier = $4)
  AND ($5 IS NULL OR i.part_number = $5);


-- =============================================================================
-- Question 2: NCRs open beyond SLA (e.g., > 30 days) + severity breakdown
-- =============================================================================

-- Open NCRs beyond SLA
SELECT
    n.ncr_id,
    n.site,
    n.supplier,
    n.part_number,
    n.severity,
    n.status,
    n.description,
    n.opened_at,
    n.days_open,
    d.filename as document_filename
FROM ncrs n
LEFT JOIN documents d ON n.document_id = d.id
WHERE n.status IN ('OPEN', 'IN_REVIEW')
  AND n.days_open > 30
ORDER BY n.days_open DESC, n.severity DESC;

-- Severity breakdown
SELECT
    n.severity,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM ncrs n
WHERE n.status IN ('OPEN', 'IN_REVIEW')
  AND n.days_open > 30
GROUP BY n.severity
ORDER BY
    CASE n.severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END;


-- =============================================================================
-- Question 3: Top failure sources (supplier, machine, part)
-- =============================================================================

-- Top failure sources by supplier
SELECT
    i.supplier,
    COUNT(*) as failure_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM inspections i
WHERE i.result = 'FAIL'
  AND i.inspection_date >= $1
  AND i.inspection_date <= $2
  AND i.supplier IS NOT NULL
GROUP BY i.supplier
ORDER BY failure_count DESC
LIMIT 10;

-- Top failure sources by part
SELECT
    i.part_number,
    i.part_description,
    COUNT(*) as failure_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM inspections i
WHERE i.result = 'FAIL'
  AND i.inspection_date >= $1
  AND i.inspection_date <= $2
  AND i.part_number IS NOT NULL
GROUP BY i.part_number, i.part_description
ORDER BY failure_count DESC
LIMIT 10;

-- Top failure sources by machine (from maintenance correlation)
SELECT
    m.machine_id,
    m.machine_description,
    COUNT(DISTINCT m.event_id) as maintenance_events,
    COUNT(DISTINCT i.inspection_id) as related_failures
FROM maintenance_events m
LEFT JOIN inspections i ON i.site = m.site
    AND i.inspection_date BETWEEN m.event_date - INTERVAL '7 days' AND m.event_date + INTERVAL '7 days'
    AND i.result = 'FAIL'
WHERE m.event_type IN ('Breakdown', 'Corrective')
  AND m.event_date >= $1
  AND m.event_date <= $2
GROUP BY m.machine_id, m.machine_description
ORDER BY maintenance_events DESC, related_failures DESC
LIMIT 10;


-- =============================================================================
-- Question 4: Evidence view: given NCR, show linked inspection + raw document references
-- =============================================================================

-- Complete evidence chain for an NCR
SELECT
    n.ncr_id,
    n.description as ncr_description,
    n.severity,
    n.status,
    n.opened_at,
    -- Linked inspection
    i.inspection_id,
    i.site as inspection_site,
    i.inspection_date,
    i.result,
    i.measurement_value,
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
WHERE n.ncr_id = $1;


-- =============================================================================
-- Question 5: Ingestion health: what failed processing and why (by stage)
-- =============================================================================

-- Processing runs with failures
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
    pr.finished_at,
    EXTRACT(EPOCH FROM (pr.finished_at - pr.started_at)) as duration_seconds
FROM processing_runs pr
LEFT JOIN documents d ON pr.document_id = d.id
WHERE pr.status IN ('FAILED', 'PARTIAL')
ORDER BY pr.started_at DESC
LIMIT 100;

-- Summary by stage
SELECT
    pr.stage,
    pr.status,
    COUNT(*) as run_count,
    SUM(pr.rows_failed) as total_rows_failed
FROM processing_runs pr
WHERE pr.started_at >= NOW() - INTERVAL '7 days'
GROUP BY pr.stage, pr.status
ORDER BY pr.stage, pr.status;


-- =============================================================================
-- Question 6: Trend view: failures per week/month
-- =============================================================================

-- Weekly failure trends
SELECT
    DATE_TRUNC('week', i.inspection_date) as week_start,
    COUNT(*) FILTER (WHERE i.result = 'FAIL') as failure_count,
    COUNT(*) as total_inspections,
    ROUND(
        COUNT(*) FILTER (WHERE i.result = 'FAIL') * 100.0 / COUNT(*),
        2
    ) as failure_rate_pct
FROM inspections i
WHERE i.inspection_date >= NOW() - INTERVAL '12 weeks'
GROUP BY DATE_TRUNC('week', i.inspection_date)
ORDER BY week_start DESC;

-- Monthly failure trends
SELECT
    DATE_TRUNC('month', i.inspection_date) as month_start,
    COUNT(*) FILTER (WHERE i.result = 'FAIL') as failure_count,
    COUNT(*) as total_inspections,
    ROUND(
        COUNT(*) FILTER (WHERE i.result = 'FAIL') * 100.0 / COUNT(*),
        2
    ) as failure_rate_pct
FROM inspections i
WHERE i.inspection_date >= NOW() - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', i.inspection_date)
ORDER BY month_start DESC;


-- =============================================================================
-- Bonus: Useful diagnostic queries
-- =============================================================================

-- Document processing status
SELECT
    d.id,
    d.filename,
    d.source,
    d.received_at,
    STRING_AGG(DISTINCT pr.stage || ':' || pr.status, ', ') as processing_status
FROM documents d
LEFT JOIN processing_runs pr ON d.id = pr.document_id
GROUP BY d.id, d.filename, d.source, d.received_at
ORDER BY d.received_at DESC;

-- Overdue NCRs by supplier
SELECT
    n.supplier,
    COUNT(*) as overdue_count,
    AVG(n.days_open) as avg_days_open,
    MAX(n.days_open) as max_days_open
FROM ncrs n
WHERE n.status IN ('OPEN', 'IN_REVIEW')
  AND n.days_open > 30
  AND n.supplier IS NOT NULL
GROUP BY n.supplier
ORDER BY overdue_count DESC;
