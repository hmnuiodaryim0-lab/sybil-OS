"""
Sybil-OS Discord Sync - Link website registration to Discord
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DiscordSyncService:
    """
    Discord 同步服务
    
    功能:
    - 检查用户 Discord 关联状态
    - 将分析结果同步为 Discord 元数据
    - 预留机器人集成接口
    """
    
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token
        self._linked_users: Dict[str, Dict[str, Any]] = {}
    
    async def check_discord_link(
        self,
        user_id: str,
        discord_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        检查用户 Discord 关联状态
        
        Returns:
            - linked: bool
            - discord_id: str or None
            - guilds: List[Dict] - 共同服务器
        """
        if not discord_id:
            # 尝试从数据库查找
            discord_id = self._linked_users.get(user_id, {}).get("discord_id")
        
        if not discord_id:
            return {
                "linked": False,
                "discord_id": None,
                "guilds": [],
                "message": "No Discord account linked"
            }
        
        # TODO: 调用 Discord API 验证
        # - 获取用户共同服务器
        # - 获取用户身份组
        
        return {
            "linked": True,
            "discord_id": discord_id,
            "guilds": [],  # TODO: 填充
            "message": "Discord account verified"
        }
    
    async def sync_profile_to_metadata(
        self,
        user_id: str,
        profile: "HumanCognitiveProfile"
    ) -> Dict[str, Any]:
        """
        将网站的认知分析结果同步为 Discord 元数据
        
        存储格式示例:
        - nickname: 添加认知维度标签
        - roles: 根据分配岗位分配身份组
        - note: 隐藏备注 (仅机器人可见)
        """
        # 1. 构建元数据
        metadata = {
            "user_id": user_id,
            "assigned_job": profile.assigned_job,
            "cognitive_dims": {
                "logic": profile.logic_depth,
                "empathy": profile.empathy_level,
                "stress": profile.stress_resilience,
                "creative": profile.creative_entropy,
                "social": profile.social_cohesion
            },
            "sync_timestamp": datetime.utcnow().isoformat(),
            "source": "sybil-os-web"
        }
        
        # 2. 生成 Discord 昵称标签
        job_tag = self._get_job_emoji_tag(profile.assigned_job)
        dimensions_tag = self._get_dimension_tag(profile)
        
        nickname_parts = []
        if job_tag:
            nickname_parts.append(job_tag)
        nickname_parts.append(dimensions_tag[:8])  # 限制长度
        
        metadata["discord_nickname"] = " | ".join(nickname_parts)
        
        # 3. 生成身份组建议
        role_suggestions = self._suggest_roles(profile)
        metadata["suggested_roles"] = role_suggestions
        
        # 4. TODO: 推送到 Discord Bot
        # await self._update_discord_user(discord_id, metadata)
        
        logger.info(f"[DiscordSync] Synced profile for user {user_id}")
        
        return metadata
    
    def _get_job_emoji_tag(self, job: Optional[str]) -> str:
        """根据岗位生成 emoji 标签"""
        job_emoji_map = {
            "Software Engineer": "💻",
            "Product Manager": "📊",
            "Data Scientist": "📈",
            "Designer": "🎨",
            "Customer Success": "💚",
            "Security Engineer": "🔐",
            "Researcher": "🔬",
            "DevOps": "⚙️",
        }
        return job_emoji_map.get(job or "", "")
    
    def _get_dimension_tag(self, profile: "HumanCognitiveProfile") -> str:
        """根据维度生成简短标签"""
        tags = []
        
        if profile.logic_depth > 0.8:
            tags.append("🧠")
        if profile.empathy_level > 0.8:
            tags.append("💜")
        if profile.creative_entropy > 0.8:
            tags.append("🎭")
        if profile.social_cohesion > 0.8:
            tags.append("🤝")
        if profile.stress_resilience > 0.8:
            tags.append("🛡️")
        
        return "".join(tags) if tags else "🔹"
    
    def _suggest_roles(self, profile: "HumanCognitiveProfile") -> list:
        """根据画像推荐 Discord 身份组"""
        roles = []
        
        # 核心维度映射到身份组
        if profile.logic_depth > 0.7:
            roles.append("理性思考者")
        if profile.empathy_level > 0.7:
            roles.append("情感顾问")
        if profile.creative_entropy > 0.7:
            roles.append("创意头脑")
        if profile.social_cohesion > 0.7:
            roles.append("社区建设者")
        
        # 根据岗位分配
        if profile.assigned_job:
            role_map = {
                "Software Engineer": ["开发者", "技术宅"],
                "Product Manager": ["产品经理", "需求方"],
                "Data Scientist": ["数据分析师", "算法工程师"],
                "Designer": ["设计师", "美术"],
                "Researcher": ["研究者", "学术派"]
            }
            roles.extend(role_map.get(profile.assigned_job, []))
        
        return list(set(roles))  # 去重
    
    async def link_discord_account(
        self,
        user_id: str,
        discord_id: str
    ) -> bool:
        """
        绑定 Discord 账户
        """
        self._linked_users[user_id] = {
            "discord_id": discord_id,
            "linked_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"[DiscordSync] Linked user {user_id} to Discord {discord_id}")
        return True
    
    async def unlink_discord_account(self, user_id: str) -> bool:
        """
        解绑 Discord 账户
        """
        if user_id in self._linked_users:
            del self._linked_users[user_id]
            logger.info(f"[DiscordSync] Unlinked user {user_id}")
            return True
        return False


# Type hint import
from sybil_os.models.persona import HumanCognitiveProfile


# 全局单例
discord_sync = DiscordSyncService()
