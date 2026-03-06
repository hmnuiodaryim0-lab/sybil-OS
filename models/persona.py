"""
Digital Soul Model - HumanCognitiveProfile
The core data model representing a citizen's cognitive profile in Sybil-OS.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class HumanCognitiveProfile(BaseModel):
    """
    Digital Soul Model - Represents a citizen's cognitive profile.
    
    All dimension scores are floats between 0.0 and 1.0.
    """
    
    # Primary identifier
    user_id: str = Field(..., description="Internal unique identifier")
    external_identity: Optional[str] = Field(
        default=None, 
        description="External ID (e.g., Discord ID, GitHub username)"
    )
    
    # Cognitive dimensions (0.0 - 1.0)
    logic_depth: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Logical reasoning capability and depth"
    )
    empathy_level: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Emotional intelligence and empathy"
    )
    stress_resilience: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Ability to handle pressure and adversity"
    )
    creative_entropy: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Creative potential and novelty-seeking"
    )
    social_cohesion: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Teamwork and social harmony capability"
    )
    
    # Vector representation (for similarity search)
    vector_summary: List[float] = Field(
        ..., 
        description="1536-dim personality embedding vector"
    )
    
    # Assignment metadata
    assigned_job: Optional[str] = Field(
        default=None,
        description="System-assigned job role"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last profile update timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "citizen_001",
                "external_identity": "discord:123456789",
                "logic_depth": 0.85,
                "empathy_level": 0.72,
                "stress_resilience": 0.68,
                "creative_entropy": 0.91,
                "social_cohesion": 0.77,
                "vector_summary": [0.1] * 1536,
                "assigned_job": "Software Architect",
                "updated_at": "2026-03-06T00:00:00Z"
            }
        }
