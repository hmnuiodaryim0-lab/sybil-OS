"""
Database connection and session management for Sybil-OS.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/sybil_os"
)

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use connection pooling in production
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI to get database session.
    
    Usage:
        @app.get("/citizens")
        def list_citizens(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from sybil_os.models.persona import HumanCognitiveProfile
    Base.metadata.create_all(bind=engine)
