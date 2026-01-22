# Compliance Dashboard - Quick Start Guide

This is your pre-workshop setup guide. Follow these steps to prepare for the workshop.

## Pre-Workshop Setup (Do This Before Session 1)

### 1. System Requirements

Install these before the workshop:
- Python 3.11 or higher
- PostgreSQL 15 or higher
- Docker Desktop (for Session 6)
- Git
- A code editor (VS Code recommended)

### 2. Clone/Setup Project

```bash
cd compliance-dashboard
```

### 3. Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.11+
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Setup PostgreSQL

**Option A: Local PostgreSQL**

```bash
# macOS with Homebrew
brew install postgresql@15
brew services start postgresql@15

# Create database user and database
createuser compliance_user -P  # Enter password: compliance_pass
createdb -O compliance_user compliance_db

# Ubuntu/Debian
sudo apt install postgresql-15
sudo -u postgres createuser compliance_user -P
sudo -u postgres createdb -O compliance_user compliance_db
```

**Option B: Docker PostgreSQL (Quick)**

```bash
docker run --name compliance-postgres \
  -e POSTGRES_DB=compliance_db \
  -e POSTGRES_USER=compliance_user \
  -e POSTGRES_PASSWORD=compliance_pass \
  -p 5432:5432 \
  -d postgres:15-alpine
```

### 6. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if you changed any defaults
# Default values should work for most setups
```

### 7. Verify Setup

```bash
# Test database connection
python -c "import psycopg2; conn = psycopg2.connect('postgresql://compliance_user:compliance_pass@localhost:5432/compliance_db'); print('✓ Database connection works!'); conn.close()"

# Test FastAPI imports
python -c "from fastapi import FastAPI; print('✓ FastAPI imports work!')"
```

## Workshop Session Workflows

### Session 1: Requirements & Schema (No Code)
**Objective:** Define questions and design schema

No setup needed - this is discussion and design on paper/whiteboard.

### Session 2: Build Database
**Objective:** Implement and initialize database

```bash
# Initialize database with schema
python scripts/init_db.py

# Verify tables were created
psql -U compliance_user -d compliance_db -c "\dt"
```

**Expected output:** Should show 5 tables (documents, processing_runs, inspections, ncrs, maintenance_events)

### Session 3: Dirty Ingestion
**Objective:** Build first working pipeline

```bash
# Copy sample data to raw folder
cp data/samples/*.csv data/raw/

# Run dirty ingestion
python worker/ingest_dirty.py

# Check what was ingested
psql -U compliance_user -d compliance_db -c "SELECT * FROM documents;"
```

### Session 4: Clean Ingestion
**Objective:** Add normalization and validation

```bash
# Reset database (fresh start)
python scripts/reset_db.py

# Re-copy sample data
cp data/samples/*.csv data/raw/

# Run clean ingestion
python worker/ingest_clean.py

# Verify data quality
psql -U compliance_user -d compliance_db -c "SELECT COUNT(*) FROM inspections;"
```

### Session 5: API & Queries
**Objective:** Implement Q&A endpoints

```bash
# Start API server
uvicorn app.main:app --reload

# In another terminal, test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/qa/failed-inspections

# Open API documentation in browser
open http://localhost:8000/docs
```

**API Endpoints to Test:**
- http://localhost:8000/docs - Interactive API documentation
- http://localhost:8000/health - Health check
- http://localhost:8000/qa/failed-inspections - Query failed inspections
- http://localhost:8000/qa/open-ncrs?older_than_days=30 - Query overdue NCRs

### Session 6: Docker Deployment
**Objective:** Containerize everything

```bash
# Build and start containers
cd docker
docker compose up

# Verify services
docker compose ps

# Test API through Docker
curl http://localhost:8000/health

# Stop services
docker compose down
```

## Common Commands Reference

### Database

```bash
# Connect to database
psql -U compliance_user -d compliance_db

# Useful SQL queries
SELECT * FROM documents;
SELECT * FROM processing_runs WHERE status = 'FAILED';
SELECT * FROM inspections WHERE result = 'FAIL';
SELECT * FROM ncrs WHERE status = 'OPEN';

# Reset database
python scripts/reset_db.py
```

### API Development

```bash
# Start API with auto-reload
uvicorn app.main:app --reload --port 8000

# Start API with specific host
uvicorn app.main:app --host 0.0.0.0 --port 8000

# View logs
tail -f logs/api.log  # If logging is configured
```

### Data Processing

```bash
# Run dirty ingestion
python worker/ingest_dirty.py

# Run clean ingestion
python worker/ingest_clean.py

# Convert CSV to PDF (optional)
python scripts/csv_to_pdf.py -i data/samples/ -o data/samples/pdf/
```

### Docker

```bash
# Start all services
docker compose up

# Start in background
docker compose up -d

# View logs
docker compose logs -f api
docker compose logs -f db

# Stop services
docker compose down

# Rebuild containers
docker compose build --no-cache
docker compose up
```

## Troubleshooting

### "Connection refused" to PostgreSQL

```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# If using Docker PostgreSQL
docker ps  # Should show postgres container running
```

### "Module not found" errors

```bash
# Make sure virtual environment is activated
which python  # Should point to your venv

# Reinstall dependencies
pip install -r requirements.txt
```

### Database already exists

```bash
# Use reset script
python scripts/reset_db.py

# Or manually drop and recreate
dropdb -U compliance_user compliance_db
createdb -U compliance_user compliance_db
python scripts/init_db.py
```

### Port 8000 already in use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
uvicorn app.main:app --port 8001
```

## Pre-Workshop Checklist

- [ ] Python 3.11+ installed and working
- [ ] PostgreSQL 15+ installed and running
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database created and accessible
- [ ] Environment file configured (`.env`)
- [ ] Database initialization successful (`python scripts/init_db.py`)
- [ ] Sample data available in `data/samples/`
- [ ] Docker installed (for Session 6)
- [ ] Code editor setup with project folder open

## Getting Help

During the workshop, if you encounter issues:

1. Check the error message carefully
2. Verify your virtual environment is activated
3. Check database connection with the verify command above
4. Ask the instructor
5. Check `README.md` for detailed documentation

## Next Steps

Once setup is complete, you're ready for Session 1!

The workshop follows this progression:
1. **Think** → Design before coding
2. **Database** → Schema first, data model defines everything
3. **Dirty** → Make it work (learn the pain points)
4. **Clean** → Make it right (engineer properly)
5. **API** → Expose answers before UI
6. **Docker** → Package for reproducibility

See you at the workshop!
