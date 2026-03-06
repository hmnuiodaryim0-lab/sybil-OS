"""
Sybil-OS API - Main Application Entry Point
"""

from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from sybil_os.database.connection import get_db, init_db
from sybil_os.models.persona import HumanCognitiveProfile


app = FastAPI(
    title="Sybil-OS",
    description="Utopian career allocation system using AI and behavioral data",
    version="0.1.0"
)


# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()


# Pydantic schemas for API requests/responses
class CognitiveProfileCreate(BaseModel):
    user_id: str
    external_identity: Optional[str] = None
    logic_depth: float
    empathy_level: float
    stress_resilience: float
    creative_entropy: float
    social_cohesion: float
    vector_summary: List[float]
    assigned_job: Optional[str] = None


class CognitiveProfileResponse(BaseModel):
    user_id: str
    external_identity: Optional[str]
    logic_depth: float
    empathy_level: float
    stress_resilience: float
    creative_entropy: float
    social_cohesion: float
    vector_summary: List[float]
    assigned_job: Optional[str]
    updated_at: datetime
    
    class Config:
        from_attributes = True


# API Routes

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "system": "Sybil-OS",
        "version": "0.1.0",
        "message": "Utopia awaits."
    }


@app.post("/profiles", response_model=CognitiveProfileResponse)
def create_profile(
    profile: CognitiveProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new citizen cognitive profile."""
    # In production, this would save to PostgreSQL
    # For now, return the input as response
    return CognitiveProfileResponse(
        **profile.model_dump(),
        updated_at=datetime.utcnow()
    )


@app.get("/profiles/{user_id}", response_model=CognitiveProfileResponse)
def get_profile(user_id: str, db: Session = Depends(get_db)):
    """Get a citizen's cognitive profile by user_id."""
    # In production, this would query from PostgreSQL
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Profile not found: {user_id}"
    )


@app.get("/health")
def health_check():
    """System health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
