# Ingestion System Guide

Complete guide to ingesting CSV and PDF files into the Compliance Dashboard.

## Overview

The ingestion system supports:
- ✅ **CSV Files** - Inspection logs, NCR reports, maintenance logs
- ✅ **PDF Files** - NCR reports, inspection certificates, maintenance work orders
- ✅ **Terminal/CLI** - Direct script execution
- ✅ **API Endpoints** - Upload and process via REST API

## Quick Start

### 1. Setup Database

```bash
# Initialize database schema
make db-init

# Or reset if already exists
make db-reset
```

### 2. Ingest CSV Files from Terminal

```bash
# Copy sample CSV files to raw folder
make sample-data

# Run clean ingestion (recommended)
make ingest-clean

# Or run dirty ingestion (for learning)
make ingest-dirty
```

### 3. Ingest PDF Files from Terminal

```bash
# Generate PDFs first (if not already done)
make gen-pdfs

# Ingest all PDFs
make ingest-pdf
```

### 4. Start API Server

```bash
# Start API with auto-reload
make api

# API will be available at: http://localhost:8000
# Interactive docs at: http://localhost:8000/docs
```

## CSV Ingestion

### Supported CSV Files

The system automatically detects file types by filename:

| Filename Pattern | Type | Table |
|-----------------|------|-------|
| `*inspection*` | Inspection logs | `inspections` |
| `*ncr*` | NCR reports | `ncrs` |
| `*maintenance*` or `*maint*` | Maintenance logs | `maintenance_events` |

### CSV Ingestion from Terminal

**Option 1: Using Makefile**

```bash
# Clean ingestion (with normalization)
make ingest-clean

# Dirty ingestion (minimal processing)
make ingest-dirty
```

**Option 2: Direct Python**

```bash
# Clean ingestion
python3 worker/ingest_clean.py

# Dirty ingestion
python3 worker/ingest_dirty.py
```

### CSV Requirements

**Inspection CSV Fields:**
- Required: `inspection_id`, `site`, `inspection_date`, `result`
- Optional: `production_line`, `supplier`, `part_number`, `inspector`, `measurement_value`, `spec_min`, `spec_max`

**NCR CSV Fields:**
- Required: `ncr_id`, `site`, `severity`, `status`, `description`, `opened_at`
- Optional: `linked_inspection_id`, `supplier`, `part_number`, `root_cause`, `corrective_action`, `closed_at`

**Maintenance CSV Fields:**
- Required: `event_id`, `site`, `machine_id`, `event_date`
- Optional: `machine_description`, `event_type`, `downtime_hours`, `technician`, `description`, `parts_replaced`

## PDF Ingestion

### Supported PDF Types

The system automatically detects PDF types by:
1. **Filename prefix**: `NCR-*`, `INS-*`, `MNT-*`
2. **Content analysis**: Searches for document type keywords

| Type | Example Filename | Keywords in Content |
|------|-----------------|---------------------|
| NCR Report | `NCR-2024-001.pdf` | "NON-CONFORMANCE", "NCR" |
| Inspection Certificate | `INS-2024-001.pdf` | "INSPECTION CERTIFICATE" |
| Maintenance Work Order | `MNT-2024-001.pdf` | "MAINTENANCE WORK ORDER" |

### PDF Ingestion from Terminal

```bash
# Ingest all PDFs in data/raw/pdf/
make ingest-pdf

# Or directly
python3 worker/ingest_pdf.py
```

### PDF Text Extraction

The system uses `pdfplumber` to extract text and parse fields:

**NCR PDFs:**
- Extracts: NCR ID, title, site, supplier, part number, severity, status, description
- Links to existing inspection records if `linked_inspection_id` found

**Inspection PDFs:**
- Extracts: Inspection ID, site, part info, measurement data, result
- Parses measurement values and spec limits

**Maintenance PDFs:**
- Extracts: Event ID, machine info, work description, technician, downtime

## API Ingestion

### Upload and Process File

**Endpoint:** `POST /upload/file/process`

Upload a file and process it immediately (recommended for UI):

```bash
# Upload CSV file
curl -X POST "http://localhost:8000/upload/file/process" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/samples/inspection_logs.csv"

# Upload PDF file
curl -X POST "http://localhost:8000/upload/file/process" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/raw/pdf/ncr/NCR-2024-001.pdf"
```

**Response:**
```json
{
  "success": true,
  "document_id": 123,
  "document_type": "inspection_csv",
  "rows_attempted": 20,
  "rows_succeeded": 20,
  "rows_failed": 0,
  "errors": null,
  "message": "Processed 20/20 rows successfully"
}
```

### Process Existing File on Server

**Endpoint:** `POST /upload/ingest/csv/{file_path}`

Process a file already on the server:

```bash
# Ingest CSV from server path
curl -X POST "http://localhost:8000/upload/ingest/csv/data/raw/inspection_logs.csv"

# Ingest PDF from server path
curl -X POST "http://localhost:8000/upload/ingest/pdf/data/raw/pdf/ncr/NCR-2024-001.pdf"
```

### Check Ingestion Status

**Endpoint:** `GET /upload/status`

Get pipeline statistics:

```bash
curl "http://localhost:8000/upload/status?limit=10"
```

**Response:**
```json
{
  "total_documents": 85,
  "total_runs": 170,
  "successful_runs": 165,
  "failed_runs": 5,
  "recent_runs": [...]
}
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload/file/process` | Upload and process file immediately |
| POST | `/upload/file` | Upload file only (no processing) |
| POST | `/upload/ingest/csv/{path}` | Process CSV from server path |
| POST | `/upload/ingest/pdf/{path}` | Process PDF from server path |
| GET | `/upload/status` | Get ingestion pipeline statistics |

## Features

### Idempotency

Files are tracked by checksum - re-running ingestion with the same file won't create duplicates:

```bash
# Safe to run multiple times
make ingest-clean
make ingest-clean  # No duplicates created
```

### Error Handling

**Row-level errors** are tracked without failing entire files:

```
Processing: inspection_logs.csv
  ✓ Success: 18/20 rows
  ✗ Failed: 2 rows
  Errors: Row 5: Invalid date format; Row 12: Missing required field
```

**Document-level tracking** in `processing_runs` table:
- Stage: RECEIVE, PARSE_CSV, NORMALIZE, VALIDATE, PERSIST
- Status: PENDING, RUNNING, SUCCESS, FAILED, PARTIAL
- Error messages and row counts stored

### Normalization

The clean ingestion pipeline (`ingest_clean.py`) includes:

**Date/Time Normalization:**
- Handles multiple date formats: YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY
- Converts timestamps to UTC

**Unit Normalization:**
- Length: standardize to mm (converts cm, m)
- Force: standardize to N (converts kN)
- Percentage: 0-100 scale

**Status Normalization:**
- Inspection results: PASS, FAIL, CONDITIONAL
- NCR status: OPEN, IN_REVIEW, CLOSED, CANCELLED
- NCR severity: LOW, MEDIUM, HIGH, CRITICAL

**String Cleaning:**
- Trim whitespace
- Handle null/empty values
- Enforce max lengths

## Verification

### Check Ingested Data

```bash
# Start API
make api

# Query inspections
curl "http://localhost:8000/qa/failed-inspections"

# Query NCRs
curl "http://localhost:8000/qa/open-ncrs?older_than_days=30"

# Check ingestion status
curl "http://localhost:8000/upload/status"
```

### Database Queries

```sql
-- Check documents
SELECT * FROM documents ORDER BY received_at DESC;

-- Check processing runs
SELECT * FROM processing_runs WHERE status = 'FAILED';

-- Check inspections
SELECT COUNT(*) FROM inspections;

-- Check NCRs
SELECT COUNT(*) FROM ncrs;

-- Check maintenance events
SELECT COUNT(*) FROM maintenance_events;
```

## Troubleshooting

### CSV Not Detected

**Problem:** File type not recognized

**Solution:** Ensure filename contains:
- `inspection` for inspection logs
- `ncr` for NCR reports
- `maintenance` or `maint` for maintenance logs

### PDF Parsing Fails

**Problem:** "Insufficient text extracted from PDF"

**Possible causes:**
- PDF is image-based (needs OCR)
- PDF is encrypted
- PDF has unusual formatting

**Solution:** Use CSV version or improve PDF parser for specific format

### Database Connection Error

**Problem:** "Connection refused" or "Database not found"

**Solution:**
```bash
# Check database is running
pg_isready -h localhost -p 5432

# Initialize database
make db-init

# Check .env configuration
cat .env | grep DB_
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'pdfplumber'`

**Solution:**
```bash
# Reinstall dependencies
make install

# Or directly
pip install -r requirements.txt
```

## Best Practices

1. **Use Clean Ingestion** - More robust than dirty version
2. **Check Status** - Monitor `/upload/status` for failures
3. **Handle Errors** - Review processing_runs table for issues
4. **Batch Processing** - Process multiple files via API
5. **Validate Data** - Check normalized values match expectations

## Example Workflow

```bash
# 1. Setup
make venv
source venv/bin/activate
make install
make db-init

# 2. Generate sample PDFs
make gen-pdfs

# 3. Ingest CSVs
make ingest-clean

# 4. Ingest PDFs
make ingest-pdf

# 5. Start API
make api

# 6. Verify in another terminal
curl "http://localhost:8000/upload/status"
curl "http://localhost:8000/qa/failed-inspections"
```

## Advanced: Custom File Types

To add support for new file types, extend:

**CSV:** Modify `worker/ingest_clean.py`
- Add new loading function
- Update `main()` to detect file type
- Add normalization rules in `worker/normalize.py`

**PDF:** Modify `worker/ingest_pdf.py`
- Add new parsing function
- Update `determine_pdf_type()` for detection
- Add field extraction patterns

## Integration with UI

The upload endpoints are designed for web UI integration:

```javascript
// Upload and process file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/upload/file/process', {
  method: 'POST',
  body: formData
});

const result = await response.json();
if (result.success) {
  console.log(`Processed ${result.rows_succeeded} rows`);
}
```

See `/docs` endpoint for interactive API documentation.
