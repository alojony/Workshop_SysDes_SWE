-- Compliance Dashboard Database Schema
-- Session 2: Build the Database First

-- Drop existing tables (for reset)
DROP TABLE IF EXISTS maintenance_events CASCADE;
DROP TABLE IF EXISTS ncrs CASCADE;
DROP TABLE IF EXISTS inspections CASCADE;
DROP TABLE IF EXISTS processing_runs CASCADE;
DROP TABLE IF EXISTS documents CASCADE;

-- Enums for status tracking
CREATE TYPE document_source AS ENUM ('CSV', 'PDF', 'API', 'MANUAL');
CREATE TYPE processing_stage AS ENUM ('RECEIVE', 'PARSE_CSV', 'NORMALIZE', 'VALIDATE', 'PERSIST');
CREATE TYPE processing_status AS ENUM ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL');
CREATE TYPE inspection_result AS ENUM ('PASS', 'FAIL', 'CONDITIONAL');
CREATE TYPE ncr_status AS ENUM ('OPEN', 'IN_REVIEW', 'CLOSED', 'CANCELLED');
CREATE TYPE ncr_severity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

-- Documents table: raw truth about ingested files
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    source document_source NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT,
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    UNIQUE(checksum),
    UNIQUE(filename, file_size_bytes)
);

CREATE INDEX idx_documents_received_at ON documents(received_at);
CREATE INDEX idx_documents_source ON documents(source);

-- Processing runs: audit trail for ingestion pipeline
CREATE TABLE processing_runs (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    stage processing_stage NOT NULL,
    status processing_status NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    rows_attempted INTEGER DEFAULT 0,
    rows_succeeded INTEGER DEFAULT 0,
    rows_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_processing_runs_document_id ON processing_runs(document_id);
CREATE INDEX idx_processing_runs_status ON processing_runs(status);
CREATE INDEX idx_processing_runs_stage ON processing_runs(stage);
CREATE INDEX idx_processing_runs_started_at ON processing_runs(started_at);

-- Inspections: facts about quality checks
CREATE TABLE inspections (
    id SERIAL PRIMARY KEY,
    inspection_id VARCHAR(100) UNIQUE NOT NULL,
    document_id INTEGER REFERENCES documents(id),
    site VARCHAR(100) NOT NULL,
    production_line VARCHAR(100),
    supplier VARCHAR(200),
    part_number VARCHAR(100),
    part_description TEXT,
    inspection_date DATE NOT NULL,
    inspector VARCHAR(200),
    result inspection_result NOT NULL,
    measurement_value DECIMAL(10,4),
    measurement_unit VARCHAR(20),
    spec_min DECIMAL(10,4),
    spec_max DECIMAL(10,4),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inspections_inspection_id ON inspections(inspection_id);
CREATE INDEX idx_inspections_date ON inspections(inspection_date);
CREATE INDEX idx_inspections_result ON inspections(result);
CREATE INDEX idx_inspections_site ON inspections(site);
CREATE INDEX idx_inspections_supplier ON inspections(supplier);
CREATE INDEX idx_inspections_part_number ON inspections(part_number);

-- NCRs: non-conformance reports with lifecycle tracking
CREATE TABLE ncrs (
    id SERIAL PRIMARY KEY,
    ncr_id VARCHAR(100) UNIQUE NOT NULL,
    document_id INTEGER REFERENCES documents(id),
    linked_inspection_id INTEGER REFERENCES inspections(id),
    site VARCHAR(100) NOT NULL,
    supplier VARCHAR(200),
    part_number VARCHAR(100),
    part_description TEXT,
    severity ncr_severity NOT NULL,
    status ncr_status NOT NULL DEFAULT 'OPEN',
    description TEXT NOT NULL,
    root_cause TEXT,
    corrective_action TEXT,
    opened_at TIMESTAMP NOT NULL,
    reviewed_at TIMESTAMP,
    closed_at TIMESTAMP,
    days_open INTEGER GENERATED ALWAYS AS (
        CASE
            WHEN closed_at IS NOT NULL THEN EXTRACT(DAY FROM (closed_at - opened_at))::INTEGER
            ELSE EXTRACT(DAY FROM (CURRENT_TIMESTAMP - opened_at))::INTEGER
        END
    ) STORED,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ncrs_ncr_id ON ncrs(ncr_id);
CREATE INDEX idx_ncrs_status ON ncrs(status);
CREATE INDEX idx_ncrs_severity ON ncrs(severity);
CREATE INDEX idx_ncrs_opened_at ON ncrs(opened_at);
CREATE INDEX idx_ncrs_days_open ON ncrs(days_open);
CREATE INDEX idx_ncrs_site ON ncrs(site);
CREATE INDEX idx_ncrs_supplier ON ncrs(supplier);
CREATE INDEX idx_ncrs_linked_inspection ON ncrs(linked_inspection_id);

-- Maintenance events: equipment maintenance logs
CREATE TABLE maintenance_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    document_id INTEGER REFERENCES documents(id),
    site VARCHAR(100) NOT NULL,
    machine_id VARCHAR(100) NOT NULL,
    machine_description TEXT,
    event_type VARCHAR(50),
    event_date DATE NOT NULL,
    downtime_hours DECIMAL(6,2),
    technician VARCHAR(200),
    description TEXT,
    parts_replaced TEXT,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_maintenance_event_id ON maintenance_events(event_id);
CREATE INDEX idx_maintenance_date ON maintenance_events(event_date);
CREATE INDEX idx_maintenance_site ON maintenance_events(site);
CREATE INDEX idx_maintenance_machine ON maintenance_events(machine_id);

-- Create a view for overdue NCRs
CREATE VIEW overdue_ncrs AS
SELECT
    n.*,
    i.inspection_id,
    i.inspection_date,
    d.filename as document_filename
FROM ncrs n
LEFT JOIN inspections i ON n.linked_inspection_id = i.id
LEFT JOIN documents d ON n.document_id = d.id
WHERE n.status IN ('OPEN', 'IN_REVIEW')
  AND n.days_open > 30;

-- Create a view for recent failures
CREATE VIEW recent_failures AS
SELECT
    i.inspection_date,
    i.site,
    i.supplier,
    i.part_number,
    i.result,
    d.filename as document_filename
FROM inspections i
LEFT JOIN documents d ON i.document_id = d.id
WHERE i.result = 'FAIL'
ORDER BY i.inspection_date DESC;
