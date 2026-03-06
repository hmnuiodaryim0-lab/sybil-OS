"""
Cognitive Analyzer - AI-powered personality analysis from Discord data
Uses LLM to generate HumanCognitiveProfile dimensions
"""

import json
import re
from typing import Dict, List, Optional, Any
import logging

from dotenv import load_dotenv
load_dotenv()

from sybil_os.core.llm_provider import get_provider, BaseLLMProvider

logger = logging.getLogger(__name__)


# System prompt for the utopia psychologist role
SYSTEM_PROMPT = """你是一位乌托邦心理评估官，负责分析人类的认知特征。

你的任务是根据用户发送的 Discord 消息文本，分析其认知维度并生成 JSON 报告。

## 评估维度

你需要评估以下5个维度（每个 0.0-1.0）：

1. **logic_depth (逻辑深度)**: 用户理性思考的能力
   - 0.0 = 完全情绪化/直觉驱动
   - 1.0 = 高度理性，系统性思考

2. **empathy_level (共情指数)**: 用户理解和感受他人情绪的能力
   - 0.0 = 冷漠，完全不考虑他人感受
   - 1.0 = 高度共情，总是考虑他人

3. **stress_resilience (抗压韧性)**: 用户面对压力和逆境的处理能力
   - 0.0 = 压力下崩溃/逃避
   - 1.0 = 压力下保持冷静积极

4. **creative_entropy (创造熵)**: 用户的创造力和思维发散程度
   - 0.0 = 极度保守，按部就班
   - 1.0 = 高度创意，思维跳跃

5. **social_cohesion (社会凝聚力)**: 用户在团队中的协调能力
   - 0.0 = 独行侠，不合群
   - 1.0 = 团队粘合剂，善于协调

## 输出格式

请直接输出 JSON，不要包含任何其他内容：

```json
{
  "logic_depth": 0.0-1.0,
  "empathy_level": 0.0-1.0,
  "stress_resilience": 0.0-1.0,
  "creative_entropy": 0.0-1.0,
  "social_cohesion": 0.0-1.0,
  "reasoning": "简短的分析理由（50字以内）"
}
```

只输出 JSON！"""


class CognitiveAnalyzer:
    """
    认知分析引擎
    
    输入: Discord 消息文本
    输出: HumanCognitiveProfile 维度分数
    """
    
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_provider()
        self.system_prompt = SYSTEM_PROMPT
    
    async def analyze(
        self,
        messages: List[Dict[str, Any]],
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        分析消息并生成认知画像
        
        Args:
            messages: 消息列表，每个消息包含 content, author, timestamp
            user_id: 可选的用户ID
            
        Returns:
            包含5个维度的字典
        """
        if not messages:
            logger.warning("No messages to analyze")
            return self._default_profile()
        
        # 构建分析文本
        text_context = self._build_context(messages)
        
        # 调用 LLM 分析
        try:
            response = await self.llm.generate(
                prompt=text_context,
                system_prompt=self.system_prompt,
                temperature=0.3,  # 低温度，结果更稳定
                max_tokens=500
            )
            
            # 解析 JSON 响应
            result = self._parse_response(response.content)
            
            if result:
                logger.info(f"Cognitive analysis complete for user {user_id}")
                return result
            else:
                logger.warning("Failed to parse LLM response, using default profile")
                return self._default_profile()
                
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return self._default_profile()
    
    def _build_context(self, messages: List[Dict[str, Any]]) -> str:
        """构建用于分析的消息上下文"""
        # 取最近50条消息
        recent = messages[-50:] if len(messages) > 50 else messages
        
        lines = []
        for msg in recent:
            author = msg.get("author_name", "Unknown")
            content = msg.get("content", "")
            if content:
                lines.append(f"{author}: {content}")
        
        context = "\n".join(lines)
        
        # 限制长度，避免超出 token 限制
        if len(context) > 8000:
            context = context[-8000:]
        
        return f"""请分析以下 Discord 消息对话，评估发消息者的认知特征：

{context}

请直接输出 JSON 结果："""
    
    def _parse_response(self, content: str) -> Optional[Dict[str, float]]:
        """解析 LLM 响应，提取 JSON"""
        # 尝试提取 JSON 块
        json_match = re.search(r'\{[\s\S]*\}', content)
        
        if not json_match:
            logger.warning(f"No JSON found in response: {content[:200]}")
            return None
        
        try:
            data = json.loads(json_match.group())
            
            # 验证必需字段
            required = ["logic_depth", "empathy_level", "stress_resilience", 
                       "creative_entropy", "social_cohesion"]
            
            for field in required:
                if field not in data:
                    logger.warning(f"Missing field: {field}")
                    return None
                
                # 确保值在 0-1 范围内
                data[field] = max(0.0, min(1.0, float(data[field])))
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return None
    
    def _default_profile(self) -> Dict[str, float]:
        """返回默认画像（当分析失败时）"""
        return {
            "logic_depth": 0.5,
            "empathy_level": 0.5,
            "stress_resilience": 0.5,
            "creative_entropy": 0.5,
            "social_cohesion": 0.5
        }
    
    async def generate_embedding(
        self,
        profile_data: Dict[str, float]
    ) -> List[float]:
        """
        根据画像维度生成 1536 维向量
        
        简单的映射方法：将5个维度扩展到1536维
        实际生产中可用更复杂的编码方式
        """
        import numpy as np
        
        # 归一化
        values = list(profile_data.values())
        
        # 扩展到固定维度
        base_vector = np.tile(values, 307)[:1536]  # 5 * 307 = 1535, 补1
        base_vector = np.append(base_vector, values[0])
        
        # 添加微小变化使其更真实
        noise = np.random.normal(0, 0.01, 1536)
        vector = base_vector + noise
        
        # 归一化到 unit vector
        vector = vector / np.linalg.norm(vector)
        
        return vector.tolist()


# 全局单例
_analyzer: Optional[CognitiveAnalyzer] = None

def get_analyzer() -> CognitiveAnalyzer:
    """获取分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = CognitiveAnalyzer()
    return _analyzer
