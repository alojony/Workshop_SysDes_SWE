# Compliance Dashboard Workshop

A 6-session workshop building a compliance Q&A system from requirements to deployment.

**Philosophy:** Design first → DB-first → build dirty → engineer it clean → expose Q&A via API → plug UI → containerize.

## Stack

- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **Containerization:** Docker (Session 6 only)
- **Data:** CSV + PDF documents

## Project Structure

```
compliance-dashboard/
├── app/                    # FastAPI application
│   ├── main.py            # API entry point
│   ├── db.py              # Database connection
│   ├── models.py          # Pydantic models
│   ├── schemas.py         # API schemas
│   ├── settings.py        # Configuration
│   └── routes/            # API endpoints
│       ├── qa.py          # Q&A endpoints
│       └── ops.py         # Operations endpoints
├── worker/                # Ingestion pipeline
│   ├── ingest_dirty.py    # Session 3: First implementation
│   ├── normalize.py       # Session 4: Data normalization
│   └── ingest_clean.py    # Session 4: Clean implementation
├── queries/               # Database queries
│   ├── qa.sql            # Reference SQL queries
│   └── qa.py             # Python query functions
├── scripts/               # Database scripts
│   ├── schema.sql        # Database schema
│   ├── init_db.py        # Initialize database
│   └── reset_db.py       # Reset database
├── data/                  # Data files
│   ├── raw/              # Incoming data files
│   └── samples/          # Sample datasets
├── docker/               # Docker configuration
│   ├── Dockerfile.api    # API container
│   └── docker-compose.yml # Complete stack
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Workshop Sessions

### Session 1: Requirements & Schema Design (No Code)
- Define compliance questions
- Draft database schema
- Design API contract

**Artifacts:** `docs/questions.md`, `docs/schema_draft.md`, `docs/api_contract.md`

### Session 2: Build the Database First
- Implement PostgreSQL schema
- Add constraints and relationships
- Create initialization scripts

**Run:**
```bash
python scripts/init_db.py
```

### Session 3: Build Dirty Ingestion
- Crude pipeline: discover → register → parse → persist
- Learn about idempotency and partial failures
- Discover how messy real data is

**Run:**
```bash
python worker/ingest_dirty.py
```

### Session 4: Engineer It Clean
- Define normalization rules
- Implement validation layer
- Improve error handling

**Run:**
```bash
python worker/ingest_clean.py
```

### Session 5: API Petitions + CLI
- Implement FastAPI endpoints
- Create query functions
- Build CLI client

**Run:**
```bash
# Start API
uvicorn app.main:app --reload

# Visit API docs
open http://localhost:8000/docs
```

### Session 6: Docker Packaging
- Containerize application
- Create docker-compose stack
- One-command deployment

**Run:**
```bash
cd docker
docker compose up
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker (for Session 6)

### Local Setup

1. **Clone and navigate to project:**
```bash
cd compliance-dashboard
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. **Initialize database:**
```bash
# Make sure PostgreSQL is running
python scripts/init_db.py
```

6. **Load sample data:**
```bash
# Copy sample files to raw data folder
cp data/samples/*.csv data/raw/

# Run ingestion
python worker/ingest_clean.py
```

7. **Start API server:**
```bash
uvicorn app.main:app --reload
```

8. **Test the API:**
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## Docker Setup (Session 6)

### Quick Start

```bash
cd docker
docker compose up
```

This starts:
- PostgreSQL database on port 5432
- FastAPI application on port 8000
- (Optional) pgAdmin on port 5050

### With pgAdmin

```bash
docker compose --profile debug up
```

Access pgAdmin at http://localhost:5050
- Email: admin@compliance.local
- Password: admin

### Stop Services

```bash
docker compose down

# Remove volumes (deletes data)
docker compose down -v
```

## Canonical Q&A Targets

The dashboard must answer these 6 questions:

1. **Failed Inspections**
   `GET /qa/failed-inspections?from=2024-01-01&to=2024-12-31&site=Factory-A`

2. **Open NCRs Beyond SLA**
   `GET /qa/open-ncrs?older_than_days=30&severity=CRITICAL`

3. **Top Failure Sources**
   `GET /qa/top-failures?group_by=supplier&from=2024-01-01&to=2024-12-31`

4. **Evidence Chain**
   `GET /qa/evidence?ncr_id=NCR-2024-001`

5. **Ingestion Health**
   `GET /ops/ingestion-runs?status=FAILED&stage=PERSIST`

6. **Failure Trends**
   `GET /qa/trends?period=week&from=2024-01-01`

## Database Schema

### Core Tables

- **documents** - Raw file registry with checksums
- **processing_runs** - Audit trail for ingestion pipeline
- **inspections** - Quality inspection facts
- **ncrs** - Non-conformance reports with lifecycle
- **maintenance_events** - Equipment maintenance logs

### Key Features

- Checksum-based idempotency
- Processing stage tracking
- Errors as data (queryable failures)
- Evidence traceability (NCR → Inspection → Document)

## Development

### Reset Database

```bash
python scripts/reset_db.py
```

⚠️ This deletes all data!

### Run Tests

```bash
pytest
```

### Code Structure

- **Models** (`app/models.py`): Database entity representations
- **Schemas** (`app/schemas.py`): API request/response contracts
- **Routes** (`app/routes/`): API endpoint handlers
- **Queries** (`queries/qa.py`): Database query functions
- **Workers** (`worker/`): Data ingestion pipeline

## Normalization Rules

### Date/Time
- All dates stored as DATE type
- Timestamps stored as TIMESTAMP (assume UTC or local factory time)
- Common formats: YYYY-MM-DD, MM/DD/YYYY

### Units
- Length: standardize to mm
- Force: standardize to N
- Percentage: store as 0-100 scale with '%' unit

### Status Enums
- Inspection: PASS, FAIL, CONDITIONAL
- NCR Status: OPEN, IN_REVIEW, CLOSED, CANCELLED
- NCR Severity: LOW, MEDIUM, HIGH, CRITICAL

### Validation
- Required fields enforced
- Duplicates prevented (by inspection_id, ncr_id, event_id)
- Invalid data captured in processing_runs, not rejected silently

## Non-Negotiable Rules

1. **Session 1:** No code allowed
2. **DB schema** must support all Q&A questions
3. **Idempotency:** Re-running ingestion doesn't duplicate data
4. **Errors are data:** Failures must be visible and queryable
5. **Docker only in Session 6**

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check credentials in .env file
cat .env | grep DB_
```

### Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

### Docker Issues

```bash
# Check container logs
docker compose logs api
docker compose logs db

# Rebuild containers
docker compose build --no-cache
docker compose up
```

## Learning Outcomes

After completing this workshop, you'll understand:

1. How to derive schema from questions (not the other way around)
2. How ingestion pipelines fail in real life
3. Why normalization matters for usability
4. How to expose "answers" via API before building UI
5. How to package systems for reproducibility
6. The value of errors-as-data architecture

## License

This is a workshop educational project. Use freely for learning.

## Contributing

This is a teaching scaffold. Participants implement the TODOs during sessions.

## Contact

For questions about the workshop, contact the instructor.
