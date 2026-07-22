"""
Mobile Operator Database - Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "Mobile Operator Database"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # PostgreSQL
    postgres_url: str = os.getenv(
        "POSTGRES_URL", 
        "postgresql://operator_admin:operator_secret_2024@localhost:5432/mobile_operator"
    )
    
    # Neo4j
    neo4j_url: str = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "neo4j_secret_2024")
    
    # CouchDB
    couchdb_url: str = os.getenv("COUCHDB_URL", "http://localhost:5984")
    couchdb_user: str = os.getenv("COUCHDB_USER", "couchdb_admin")
    couchdb_password: str = os.getenv("COUCHDB_PASSWORD", "couchdb_secret_2024")
    couchdb_database: str = "service_requests"
    
    # Payment settings
    payment_delay_days_for_disconnection: int = 30  # Days until disconnection warning
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
