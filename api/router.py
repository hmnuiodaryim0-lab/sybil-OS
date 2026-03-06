"""
Sybil-OS API Routes - v1 Endpoints
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from sybil_os.database.connection import get_db
from sybil_os.models.persona import HumanCognitiveProfile, BirthInfo
from sybil_os.models.project import ProjectRequirement, DimensionRequirement
from sybil_os.core.observer_registry import (
    TelemetryPacket, ObserverType, DataPriority, registry
)


router = APIRouter(prefix="/v1", tags=["v1"])


# ==================== Request/Response Models ====================

class RegisterRequest(BaseModel):
    """用户注册请求"""
    user_id: str
    external_identity: Optional[str] = None
    identity_type: str = "job_seeker"
    birth_datetime: Optional[datetime] = None
    birth_timezone: Optional[str] = "Asia/Shanghai"
    resume_raw: Optional[str] = None


class RegisterResponse(BaseModel):
    """用户注册响应"""
    user_id: str
    status: str
    message: str
    assigned_job: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    """项目创建请求"""
    project_id: str
    project_name: str
    owner_id: str
    job_title: str
    job_description: str
    dimension_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    vector_similarity_threshold: float = 0.75
    salary_range: Optional[str] = None
    headcount: int = 1
    tags: List[str] = Field(default_factory=list)


class ProjectCreateResponse(BaseModel):
    """项目创建响应"""
    project_id: str
    job_title: str
    status: str
    created_at: datetime


class TelemetryPushRequest(BaseModel):
    """遥测数据推送请求"""
    observer_id: str
    observer_type: str
    data: Dict[str, Any]
    priority: str = "normal"
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class TelemetryPushResponse(BaseModel):
    """遥测数据推送响应"""
    packet_id: str
    status: str
    timestamp: datetime


# ==================== Routes ====================

@router.post("/register", response_model=RegisterResponse)
async def register_user(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    用户注册接口
    
    支持:
    - 上传简历 (resume_raw)
    - 提交生辰信息 (birth_datetime)
    - 指定身份类型 (job_seeker / founder / investor)
    """
    # 1. 构建生辰信息
    birth_info = None
    if request.birth_datetime:
        birth_info = BirthInfo(
            birth_datetime=request.birth_datetime,
            timezone=request.birth_timezone or "Asia/Shanghai"
        )
    
    # 2. 创建认知档案 (placeholder - 实际需要 AI 分析)
    profile = HumanCognitiveProfile(
        user_id=request.user_id,
        external_identity=request.external_identity,
        identity_type=request.identity_type,
        logic_depth=0.5,  # TODO: AI 分析得出
        empathy_level=0.5,
        stress_resilience=0.5,
        creative_entropy=0.5,
        social_cohesion=0.5,
        vector_summary=[0.0] * 1536,  # TODO: 生成 embedding
        birth_info=birth_info,
        resume_raw=request.resume_raw,
        updated_at=datetime.utcnow()
    )
    
    # 3. TODO: 保存到数据库
    # db.add(profile)
    # db.commit()
    
    # 4. TODO: 触发 Discord 同步 (后台任务)
    # if request.external_identity:
    #     background_tasks.add_task(sync_to_discord, profile)
    
    return RegisterResponse(
        user_id=request.user_id,
        status="registered",
        message="Profile created successfully. AI analysis pending.",
        assigned_job=None
    )


@router.post("/project/create", response_model=ProjectCreateResponse)
async def create_project_requirement(
    request: ProjectCreateRequest,
    db: Session = Depends(get_db)
):
    """
    项目方发布用人需求
    
    支持指定所需维度向量:
    - logic_depth, empathy_level, stress_resilience
    - creative_entropy, social_cohesion
    """
    # 1. 解析维度要求
    dimensions = [
        DimensionRequirement(
            dimension=d.get("dimension"),
            min_value=d.get("min_value", 0.0),
            max_value=d.get("max_value", 1.0),
            weight=d.get("weight", 1.0)
        )
        for d in request.dimension_requirements
    ]
    
    # 2. 创建项目需求
    project = ProjectRequirement(
        project_id=request.project_id,
        project_name=request.project_name,
        owner_id=request.owner_id,
        job_title=request.job_title,
        job_description=request.job_description,
        required_dimensions=dimensions,
        vector_similarity_threshold=request.vector_similarity_threshold,
        salary_range=request.salary_range,
        headcount=request.headcount,
        tags=request.tags,
        status="open"
    )
    
    # 3. TODO: 保存到数据库
    
    return ProjectCreateResponse(
        project_id=request.project_id,
        job_title=request.job_title,
        status="open",
        created_at=datetime.utcnow()
    )


@router.post("/telemetry/push", response_model=TelemetryPushResponse)
async def push_telemetry(
    request: TelemetryPushRequest
):
    """
    通用遥测数据推送接口
    
    用于接收未来摄像头、截屏等监控模块的分析碎片:
    - observer_type: camera / screen / chat / keyboard
    - data: 具体的监控数据
    - priority: low / normal / high / critical
    """
    # 1. 验证 observer 类型
    try:
        obs_type = ObserverType(request.observer_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid observer_type: {request.observer_type}"
        )
    
    # 2. 解析优先级
    try:
        priority = DataPriority(request.priority)
    except ValueError:
        priority = DataPriority.NORMAL
    
    # 3. 创建遥测数据包
    packet = TelemetryPacket(
        observer_id=request.observer_id,
        observer_type=obs_type,
        timestamp=datetime.utcnow(),
        data=request.data,
        priority=priority,
        session_id=request.session_id,
        user_id=request.user_id
    )
    
    # 4. TODO: 存入时序数据库 / 消息队列
    # await telemetry_store.write(packet)
    
    # 5. 检查是否有实时订阅者
    observer = registry.get(request.observer_id)
    if observer:
        observer._emit(packet)
    
    return TelemetryPushResponse(
        packet_id=f"pkg_{datetime.utcnow().timestamp()}",
        status="accepted",
        timestamp=datetime.utcnow()
    )


@router.get("/observers")
async def list_observers():
    """列出所有已注册的 Observer"""
    return registry.status()


@router.post("/observers/{observer_type}/{observer_id}/start")
async def start_observer(observer_type: str, observer_id: str):
    """启动指定 Observer"""
    observer = registry.get(observer_id)
    if not observer:
        raise HTTPException(status_code=404, detail="Observer not found")
    
    success = await observer.start()
    return {"observer_id": observer_id, "started": success}


@router.post("/observers/{observer_id}/stop")
async def stop_observer(observer_id: str):
    """停止指定 Observer"""
    observer = registry.get(observer_id)
    if not observer:
        raise HTTPException(status_code=404, detail="Observer not found")
    
    success = await observer.stop()
    return {"observer_id": observer_id, "stopped": success}
