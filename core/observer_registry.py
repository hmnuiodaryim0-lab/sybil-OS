"""
Observer Registry - Plugin Architecture for Monitoring Adapters
高度模块化的监控适配器注册中心，支持热插拔
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ObserverType(Enum):
    """Observer 类型枚举"""
    CAMERA = "camera"           # 视觉监控
    SCREEN = "screen"           # 截屏分析
    CHAT = "chat"               # 聊天分析
    KEYBOARD = "keyboard"       # 键盘行为
    FILESYSTEM = "filesystem"   # 文件操作
    CUSTOM = "custom"           # 自定义


class DataPriority(Enum):
    """数据优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ObserverConfig:
    """Observer 配置"""
    enabled: bool = True
    sample_rate_hz: float = 1.0
    buffer_size: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TelemetryPacket:
    """遥测数据封装"""
    observer_id: str
    observer_type: ObserverType
    timestamp: datetime
    data: Dict[str, Any]
    priority: DataPriority = DataPriority.NORMAL
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class BaseObserver(ABC):
    """
    Observer 基类 - 所有监控适配器的父接口
    
    设计原则:
    - 插件化: 可随时注册/注销
    - 标准化: 统一的数据接口
    - 异步: 支持异步数据采集
    """
    
    def __init__(self, observer_id: str, config: Optional[ObserverConfig] = None):
        self.observer_id = observer_id
        self.config = config or ObserverConfig()
        self._is_running = False
        self._callbacks: List[Callable] = []
    
    @property
    @abstractmethod
    def observer_type(self) -> ObserverType:
        """返回 Observer 类型"""
        pass
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @abstractmethod
    async def start(self) -> bool:
        """启动监控"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """停止监控"""
        pass
    
    @abstractmethod
    async def collect(self) -> Optional[TelemetryPacket]:
        """采集单次数据"""
        pass
    
    def on_data(self, callback: Callable[[TelemetryPacket], None]):
        """注册数据回调"""
        self._callbacks.append(callback)
    
    def _emit(self, packet: TelemetryPacket):
        """触发回调"""
        for cb in self._callbacks:
            try:
                cb(packet)
            except Exception as e:
                logger.error(f"Callback error in {self.observer_id}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "observer_id": self.observer_id,
            "type": self.observer_type.value,
            "running": self._is_running,
            "config": {
                "enabled": self.config.enabled,
                "sample_rate_hz": self.config.sample_rate_hz
            }
        }


class CameraObserver(BaseObserver):
    """
    视觉监控适配器 - Camera Observer
    
    接口预留:
    - 面部识别 / 表情分析
    - 眼神追踪
    - 注意力检测
    - 环境识别
    """
    
    @property
    def observer_type(self) -> ObserverType:
        return ObserverType.CAMERA
    
    async def start(self) -> bool:
        """启动摄像头监控"""
        logger.info(f"[CameraObserver] Starting {self.observer_id}")
        # TODO: 初始化摄像头
        # TODO: 加载视觉模型
        self._is_running = True
        return True
    
    async def stop(self) -> bool:
        """停止摄像头监控"""
        logger.info(f"[CameraObserver] Stopping {self.observer_id}")
        # TODO: 释放资源
        self._is_running = False
        return True
    
    async def collect(self) -> Optional[TelemetryPacket]:
        """
        采集视觉数据
        
        返回字段示例:
        - face_detected: bool
        - emotion: Dict[str, float]
        - gaze_direction: Tuple[float, float]
        - attention_score: float
        """
        if not self._is_running:
            return None
        
        # Placeholder - 返回模拟数据
        return TelemetryPacket(
            observer_id=self.observer_id,
            observer_type=self.observer_type,
            timestamp=datetime.utcnow(),
            data={
                "face_detected": True,
                "emotion": {"neutral": 0.7, "focused": 0.3},
                "gaze_direction": (0.5, 0.5),
                "attention_score": 0.85
            },
            priority=DataPriority.HIGH
        )


class ScreenObserver(BaseObserver):
    """
    截屏分析适配器 - Screen Observer
    
    接口预留:
    - 屏幕内容 OCR
    - 应用窗口识别
    - 工作效率分析
    - 敏感信息检测
    """
    
    @property
    def observer_type(self) -> ObserverType:
        return ObserverType.SCREEN
    
    async def start(self) -> bool:
        """启动截屏监控"""
        logger.info(f"[ScreenObserver] Starting {self.observer_id}")
        # TODO: 初始化屏幕捕获
        self._is_running = True
        return True
    
    async def stop(self) -> bool:
        """停止截屏监控"""
        logger.info(f"[ScreenObserver] Stopping {self.observer_id}")
        self._is_running = False
        return True
    
    async def collect(self) -> Optional[TelemetryPacket]:
        """
        采集屏幕数据
        
        返回字段示例:
        - active_window: str
        - screenshot_hash: str
        - ocr_text: List[str]
        - productivity_score: float
        """
        if not self._is_running:
            return None
        
        return TelemetryPacket(
            observer_id=self.observer_id,
            observer_type=self.observer_type,
            timestamp=datetime.utcnow(),
            data={
                "active_window": "VS Code",
                "screenshot_hash": "abc123",
                "ocr_text": ["def main():", "    pass"],
                "productivity_score": 0.92
            },
            priority=DataPriority.NORMAL
        )


class ChatObserver(BaseObserver):
    """
    聊天分析适配器 - Chat Observer
    
    接口预留:
    - 消息情感分析
    - 响应时间统计
    - 交互模式识别
    - 关键词提取
    """
    
    @property
    def observer_type(self) -> ObserverType:
        return ObserverType.CHAT
    
    async def start(self) -> bool:
        """启动聊天监控"""
        logger.info(f"[ChatObserver] Starting {self.observer_id}")
        self._is_running = True
        return True
    
    async def stop(self) -> bool:
        """停止聊天监控"""
        logger.info(f"[ChatObserver] Stopping {self.observer_id}")
        self._is_running = False
        return True
    
    async def collect(self) -> Optional[TelemetryPacket]:
        """
        采集聊天数据
        """
        if not self._is_running:
            return None
        
        return TelemetryPacket(
            observer_id=self.observer_id,
            observer_type=self.observer_type,
            timestamp=datetime.utcnow(),
            data={
                "message_count": 42,
                "avg_response_time_sec": 3.2,
                "sentiment": {"positive": 0.6, "neutral": 0.3, "negative": 0.1},
                "engagement_score": 0.78
            },
            priority=DataPriority.NORMAL
        )


class ObserverRegistry:
    """
    Observer 注册中心 - 插件管理器
    
    支持:
    - 注册/注销 Observer
    - 批量启动/停止
    - 查找 Observer
    - 事件分发
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._observers: Dict[str, BaseObserver] = {}
        return cls._instance
    
    def register(self, observer: BaseObserver) -> bool:
        """注册 Observer"""
        if observer.observer_id in self._observers:
            logger.warning(f"Observer {observer.observer_id} already registered")
            return False
        
        self._observers[observer.observer_id] = observer
        logger.info(f"Registered observer: {observer.observer_id} ({observer.observer_type.value})")
        return True
    
    def unregister(self, observer_id: str) -> bool:
        """注销 Observer"""
        if observer_id not in self._observers:
            return False
        
        observer = self._observers.pop(observer_id)
        if observer.is_running:
            import asyncio
            asyncio.create_task(observer.stop())
        
        logger.info(f"Unregistered observer: {observer_id}")
        return True
    
    def get(self, observer_id: str) -> Optional[BaseObserver]:
        """获取 Observer"""
        return self._observers.get(observer_id)
    
    def list_observers(self, observer_type: Optional[ObserverType] = None) -> List[BaseObserver]:
        """列出所有 Observer"""
        if observer_type:
            return [o for o in self._observers.values() if o.observer_type == observer_type]
        return list(self._observers.values())
    
    async def start_all(self) -> Dict[str, bool]:
        """启动所有 Observer"""
        results = {}
        for obs in self._observers.values():
            if obs.config.enabled:
                results[obs.observer_id] = await obs.start()
        return results
    
    async def stop_all(self) -> Dict[str, bool]:
        """停止所有 Observer"""
        results = {}
        for obs in self._observers.values():
            results[obs.observer_id] = await obs.stop()
        return results
    
    def status(self) -> Dict[str, Any]:
        """获取注册表状态"""
        return {
            "total_observers": len(self._observers),
            "observers": {
                obs_id: {
                    "type": obs.observer_type.value,
                    "running": obs.is_running,
                    "enabled": obs.config.enabled
                }
                for obs_id, obs in self._observers.items()
            }
        }


# 全局单例
registry = ObserverRegistry()


# 注册默认 Observer 工厂
OBSERVER_FACTORIES: Dict[ObserverType, type] = {
    ObserverType.CAMERA: CameraObserver,
    ObserverType.SCREEN: ScreenObserver,
    ObserverType.CHAT: ChatObserver,
}


def create_observer(
    observer_type: ObserverType,
    observer_id: str,
    config: Optional[ObserverConfig] = None
) -> Optional[BaseObserver]:
    """Observer 工厂函数"""
    factory = OBSERVER_FACTORIES.get(observer_type)
    if factory:
        return factory(observer_id, config)
    return None
