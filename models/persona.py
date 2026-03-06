"""
Digital Soul Model - Extended HumanCognitiveProfile
With birth info, resume, and identity type support.
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from pydantic import field_validator


class BirthInfo(BaseModel):
    """生辰信息 - Birth details for destiny analysis."""
    birth_datetime: datetime = Field(..., description="出生日期时间")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    latitude: Optional[float] = Field(default=None, description="出生纬度")
    longitude: Optional[float] = Field(default=None, description="出生经度")
    lunar_calendar: Optional[bool] = Field(default=True, description="是否使用农历")


class HumanCognitiveProfile(BaseModel):
    """
    Digital Soul Model - Extended citizen cognitive profile.
    """
    
    # Identity
    user_id: str = Field(..., description="Internal unique identifier")
    external_identity: Optional[str] = Field(
        default=None, 
        description="External ID (e.g., Discord ID)"
    )
    
    # Identity type
    identity_type: Literal["job_seeker", "founder", "investor", "observer"] = Field(
        default="job_seeker",
        description="User role in the system"
    )
    
    # Cognitive dimensions (0.0 - 1.0)
    logic_depth: float = Field(
        ..., ge=0.0, le=1.0,
        description="Logical reasoning capability"
    )
    empathy_level: float = Field(
        ..., ge=0.0, le=1.0,
        description="Emotional intelligence"
    )
    stress_resilience: float = Field(
        ..., ge=0.0, le=1.0,
        description="Pressure handling ability"
    )
    creative_entropy: float = Field(
        ..., ge=0.0, le=1.0,
        description="Creative potential"
    )
    social_cohesion: float = Field(
        ..., ge=0.0, le=1.0,
        description="Teamwork capability"
    )
    
    # Vector representation
    vector_summary: List[float] = Field(
        ...,
        description="Personality embedding vector"
    )
    
    # Extended data
    birth_info: Optional[BirthInfo] = Field(
        default=None,
        description="生辰信息 for destiny analysis"
    )
    resume_raw: Optional[str] = Field(
        default=None,
        description="原始简历内容"
    )
    
    # Assignment
    assigned_job: Optional[str] = Field(default=None)
    assigned_project: Optional[str] = Field(default=None)
    
    # Metadata
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    discord_linked: bool = Field(default=False)
    
    @field_validator("vector_summary")
    @classmethod
    def validate_vector_dim(cls, v):
        if len(v) not in (768, 1536, 2048):
            raise ValueError(f"Vector dimension must be 768, 1536, or 2048, got {len(v)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "citizen_001",
                "external_identity": "discord:123456789",
                "identity_type": "job_seeker",
                "logic_depth": 0.85,
                "empathy_level": 0.72,
                "stress_resilience": 0.68,
                "creative_entropy": 0.91,
                "social_cohesion": 0.77,
                "vector_summary": [0.1] * 1536,
                "birth_info": {
                    "birth_datetime": "1984-03-25T06:30:00",
                    "timezone": "Asia/Shanghai"
                },
                "assigned_job": "Software Architect"
            }
        }
