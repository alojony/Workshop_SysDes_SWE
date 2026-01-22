# Compliance Dashboard - Makefile
# Convenient commands for workshop sessions

.PHONY: help install db-init db-reset ingest-dirty ingest-clean api docker-up docker-down test clean

# Default target
help:
	@echo "Compliance Dashboard - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make venv         - Create Python virtual environment"
	@echo "  make install      - Install Python dependencies"
	@echo "  make db-init      - Initialize database schema"
	@echo "  make db-reset     - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Session Commands:"
	@echo "  make ingest-dirty - Run dirty CSV ingestion (Session 3)"
	@echo "  make ingest-clean - Run clean CSV ingestion (Session 4)"
	@echo "  make ingest-pdf   - Run PDF ingestion"
	@echo "  make api          - Start FastAPI server (Session 5)"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up    - Start Docker containers (Session 6)"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make docker-logs  - View Docker logs"
	@echo ""
	@echo "PDF Generation Commands:"
	@echo "  make gen-pdfs     - Generate all PDF documents"
	@echo "  make gen-ncr      - Generate NCR PDFs only"
	@echo "  make gen-inspect  - Generate Inspection PDFs only"
	@echo "  make gen-maint    - Generate Maintenance PDFs only"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean up temporary files"
	@echo "  make sample-data  - Copy sample data to raw folder"
	@echo ""

# Setup
venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Virtual environment created!"
	@echo "Activate it with: source venv/bin/activate"

install:
	@echo "Installing dependencies..."
	python3 -m pip install -r requirements.txt
	@echo "Installation complete!"

# Database operations
db-init:
	@echo "Initializing database..."
	python3 scripts/init_db.py

db-reset:
	@echo "WARNING: This will delete all data!"
	python3 scripts/reset_db.py

# Data ingestion
sample-data:
	@echo "Copying sample data to raw folder..."
	cp data/samples/*.csv data/raw/
	@echo "Sample data ready for ingestion"

ingest-dirty: sample-data
	@echo "Running dirty ingestion..."
	python3 worker/ingest_dirty.py

ingest-clean: sample-data
	@echo "Running clean ingestion..."
	python3 worker/ingest_clean.py

ingest-pdf:
	@echo "Running PDF ingestion..."
	python3 worker/ingest_pdf.py

# API
api:
	@echo "Starting FastAPI server..."
	@echo "API docs: http://localhost:8000/docs"
	uvicorn app.main:app --reload

# Docker
docker-up:
	@echo "Starting Docker containers..."
	cd docker && docker compose up

docker-down:
	@echo "Stopping Docker containers..."
	cd docker && docker compose down

docker-logs:
	cd docker && docker compose logs -f

docker-rebuild:
	@echo "Rebuilding Docker containers..."
	cd docker && docker compose build --no-cache && docker compose up

# Testing
test:
	pytest

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete"

# PDF Generation
gen-pdfs:
	@echo "Generating all PDF documents..."
	python3 scripts/generate_all_pdfs.py

gen-ncr:
	@echo "Generating NCR PDFs..."
	python3 scripts/generate_ncr_pdfs.py

gen-inspect:
	@echo "Generating Inspection Certificate PDFs..."
	python3 scripts/generate_inspection_pdfs.py

gen-maint:
	@echo "Generating Maintenance Work Order PDFs..."
	python3 scripts/generate_maintenance_pdfs.py

# Full reset and restart workflow
fresh-start: clean db-reset db-init ingest-clean
	@echo ""
	@echo "=========================================="
	@echo "Fresh start complete!"
	@echo "Database reset, schema initialized, and clean data ingested"
	@echo "Run 'make api' to start the API server"
	@echo "=========================================="
