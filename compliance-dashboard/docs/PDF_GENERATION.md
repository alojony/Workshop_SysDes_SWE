## PDF Document Generation

The workshop includes scripts to generate realistic compliance PDF documents for testing ingestion and document linking features.

### Document Types

1. **NCR Reports** (Non-Conformance Reports)
   - 4-page professional forms
   - 50 detailed NCR documents
   - Includes: NCR identification, details, review board, actions, attachments
   - Output: `data/raw/pdf/ncr/NCR-2024-XXX.pdf`

2. **Inspection Certificates**
   - Professional inspection reports
   - 20 inspection certificates
   - Includes: part info, measurement results, pass/fail status
   - Output: `data/raw/pdf/inspections/INS-2024-XXX.pdf`

3. **Maintenance Work Orders**
   - Equipment maintenance documentation
   - 15 work order PDFs
   - Includes: equipment info, work description, parts replaced
   - Output: `data/raw/pdf/maintenance/MNT-2024-XXX.pdf`

### Quick Start

```bash
# Install dependencies (includes reportlab)
make install

# Generate all PDFs (85 documents total)
make gen-pdfs

# Or generate individually
make gen-ncr       # 50 NCR PDFs
make gen-inspect   # 20 Inspection PDFs
make gen-maint     # 15 Maintenance PDFs
```

### Manual Usage

```bash
# Generate NCR PDFs
python scripts/generate_ncr_pdfs.py -i data/samples/ncr_detailed.csv -o data/raw/pdf/ncr

# Generate Inspection PDFs
python scripts/generate_inspection_pdfs.py -i data/samples/inspection_logs.csv -o data/raw/pdf/inspections

# Generate Maintenance PDFs
python scripts/generate_maintenance_pdfs.py -i data/samples/maintenance_logs.csv -o data/raw/pdf/maintenance
```

### Data Sources

- **NCR PDFs**: Generated from `data/samples/ncr_detailed.csv` (50 records)
- **Inspection PDFs**: Generated from `data/samples/inspection_logs.csv` (20 records)
- **Maintenance PDFs**: Generated from `data/samples/maintenance_logs.csv` (15 records)

### Features

**NCR Reports:**
- Multi-page layout matching professional forms
- Linked to inspection records
- Status tracking (OPEN, IN_REVIEW, CLOSED)
- Severity levels (LOW, MEDIUM, HIGH, CRITICAL)
- Review board details
- Actions and attachments tracking

**Inspection Certificates:**
- Pass/Fail/Conditional status with color coding
- Measurement data with specifications
- Inspector information
- Electronic certificate format

**Maintenance Work Orders:**
- Equipment identification
- Work type (Preventive, Corrective, Breakdown)
- Downtime tracking
- Parts replacement records
- Technician information

### Workshop Usage

These PDFs simulate realistic compliance documents for:

**Session 3-4: Document Ingestion**
- Test file discovery and registration
- Checksum-based idempotency
- Processing stage tracking
- PDF parsing (optional extension)

**Session 5: Evidence Linking**
- Demonstrate NCR → Inspection → Document traceability
- Query evidence chains
- Show document references in API responses

**Future Extensions:**
- PDF text extraction
- Automatic field parsing
- OCR for scanned documents
- Document classification

### File Structure

```
data/raw/pdf/
├── ncr/
│   ├── NCR-2024-001.pdf
│   ├── NCR-2024-002.pdf
│   └── ... (50 total)
├── inspections/
│   ├── INS-2024-001.pdf
│   ├── INS-2024-002.pdf
│   └── ... (20 total)
└── maintenance/
    ├── MNT-2024-001.pdf
    ├── MNT-2024-002.pdf
    └── ... (15 total)
```

### Customization

To create your own PDFs:

1. **Modify CSV data**: Edit the CSV files in `data/samples/`
2. **Adjust layout**: Edit the generator scripts in `scripts/`
3. **Add fields**: Update both CSV and generator code
4. **Change styling**: Modify colors, fonts, layouts in generator scripts

### Tips

- Generated PDFs are ~50-100KB each (total ~7-8MB)
- PDFs include realistic manufacturing data
- NCR PDFs link to corresponding inspection records
- Dates are realistic (2024 calendar year)
- Supplier names, part numbers match across documents
