"""
Project Requirement Model - For founders to publish job openings
"""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class DimensionRequirement(BaseModel):
    """单维度要求 - Single dimension requirement."""
    dimension: str = Field(..., description="维度名称")
    min_value: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    max_value: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    weight: float = Field(default=1.0, ge=0.0, le=2.0, description="权重")


class ProjectRequirement(BaseModel):
    """
    Project Job Requirement - 岗位需求模型
    """
    project_id: str = Field(..., description="项目唯一ID")
    project_name: str = Field(..., description="项目名称")
    owner_id: str = Field(..., description="项目所有者 user_id")
    
    # Job details
    job_title: str = Field(..., description="职位名称")
    job_description: str = Field(..., description="职位描述")
    
    # Required cognitive dimensions (0.0 - 1.0)
    required_dimensions: List[DimensionRequirement] = Field(
        default_factory=list,
        description="所需认知维度要求"
    )
    
    # Vector similarity threshold
    vector_similarity_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="向量匹配阈值"
    )
    
    # Salary / compensation
    salary_range: Optional[str] = Field(default=None)
    equity: Optional[str] = Field(default=None)
    
    # Status
    status: str = Field(default="open", description="open/closed/paused")
    headcount: int = Field(default=1, ge=1)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    
    def get_dimension_dict(self) -> Dict[str, float]:
        """转换为维度字典，便于匹配计算"""
        return {d.dimension: d.weight for d in self.required_dimensions}
    
    def check_candidate(self, profile: "HumanCognitiveProfile") -> Dict:
        """检查候选人是否符合要求"""
        passed = []
        failed = []
        
        for dim_req in self.required_dimensions:
            value = getattr(profile, dim_req.dimension, None)
            if value is None:
                failed.append(dim_req.dimension)
                continue
                
            in_range = (
                (dim_req.min_value or 0) <= value <= (dim_req.max_value or 1)
            )
            if in_range:
                passed.append(dim_req.dimension)
            else:
                failed.append(dim_req.dimension)
        
        return {
            "passed": passed,
            "failed": failed,
            "match_rate": len(passed) / max(len(self.required_dimensions), 1)
        }
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_001",
                "project_name": "AI Startup",
                "owner_id": "founder_001",
                "job_title": "Senior ML Engineer",
                "job_description": "Build LLM applications",
                "required_dimensions": [
                    {"dimension": "logic_depth", "min_value": 0.8, "weight": 1.5},
                    {"dimension": "creative_entropy", "min_value": 0.7, "weight": 1.0}
                ],
                "vector_similarity_threshold": 0.80,
                "salary_range": "$150k-$200k",
                "status": "open",
                "headcount": 2
            }
        }


# Import for type hint
from sybil_os.models.persona import HumanCognitiveProfile
