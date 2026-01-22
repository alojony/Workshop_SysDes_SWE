"""
Application settings and configuration
Loads from environment variables
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # Database
    database_url: str = "postgresql://compliance_user:compliance_pass@localhost:5432/compliance_db"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "compliance_db"
    db_user: str = "compliance_user"
    db_password: str = "compliance_pass"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    log_level: str = "INFO"

    # Data paths
    raw_data_path: str = "./data/raw"
    samples_data_path: str = "./data/samples"

    # Processing
    max_workers: int = 4
    batch_size: int = 100
    checksum_algorithm: str = "sha256"

    # NCR SLA
    ncr_sla_warning_days: int = 20
    ncr_sla_critical_days: int = 30

    # Environment
    environment: str = "development"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
