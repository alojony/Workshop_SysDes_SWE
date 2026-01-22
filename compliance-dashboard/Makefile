# Compliance Dashboard - Makefile
# Convenient commands for workshop sessions

.PHONY: help install db-init db-reset ingest-dirty ingest-clean api docker-up docker-down test clean

# Default target
help:
	@echo "Compliance Dashboard - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make db-init      - Initialize database schema"
	@echo "  make db-reset     - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Session Commands:"
	@echo "  make ingest-dirty - Run dirty ingestion (Session 3)"
	@echo "  make ingest-clean - Run clean ingestion (Session 4)"
	@echo "  make api          - Start FastAPI server (Session 5)"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up    - Start Docker containers (Session 6)"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make docker-logs  - View Docker logs"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean up temporary files"
	@echo "  make sample-data  - Copy sample data to raw folder"
	@echo ""

# Setup
install:
	pip install -r requirements.txt

# Database operations
db-init:
	@echo "Initializing database..."
	python scripts/init_db.py

db-reset:
	@echo "WARNING: This will delete all data!"
	python scripts/reset_db.py

# Data ingestion
sample-data:
	@echo "Copying sample data to raw folder..."
	cp data/samples/*.csv data/raw/
	@echo "Sample data ready for ingestion"

ingest-dirty: sample-data
	@echo "Running dirty ingestion..."
	python worker/ingest_dirty.py

ingest-clean: sample-data
	@echo "Running clean ingestion..."
	python worker/ingest_clean.py

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

# Full reset and restart workflow
fresh-start: clean db-reset db-init ingest-clean
	@echo ""
	@echo "=========================================="
	@echo "Fresh start complete!"
	@echo "Database reset, schema initialized, and clean data ingested"
	@echo "Run 'make api' to start the API server"
	@echo "=========================================="
