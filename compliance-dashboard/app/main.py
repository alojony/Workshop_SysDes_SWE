"""
Compliance Dashboard FastAPI Application
Main entry point for the API server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import psycopg2
from app.settings import settings
from app.schemas import HealthResponse
from app.routes import qa, ops, upload

# Create FastAPI app
app = FastAPI(
    title="Compliance Dashboard API",
    description="Q&A API for compliance and quality control data",
    version="1.0.0"
)

# CORS middleware for UI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(qa.router)
app.include_router(ops.router)
app.include_router(upload.router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Verifies API and database connectivity
    """
    db_status = "unknown"

    try:
        # Try to connect to database
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password
        )
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        timestamp=datetime.now(),
        database=db_status
    )


@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": "Compliance Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
