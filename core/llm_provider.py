"""
LLM Provider - Unified interface for AI model access
Supports OpenAI, Anthropic, and local models via python-dotenv
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


# Environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    model: str
    usage: Dict[str, int]
    raw_response: Optional[Dict] = None


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> LLMResponse:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding vector"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider (GPT-4, GPT-3.5, text-embedding-ada-002)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.client = None
        
        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("openai package not installed")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = "gpt-4o",
        **kwargs
    ) -> LLMResponse:
        if not self.client:
            raise RuntimeError("OpenAI client not initialized. Check API key.")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            raw_response=response.model_dump()
        )
    
    async def embed(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        if not self.client:
            raise RuntimeError("OpenAI client not initialized. Check API key.")
        
        response = await self.client.embeddings.create(
            model=model,
            input=text
        )
        
        return response.data[0].embedding


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider (Claude 3)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        self.client = None
        
        if self.api_key and self.api_key != "your_anthropic_api_key_here":
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("anthropic package not installed")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = "claude-3-opus-20240229",
        **kwargs
    ) -> LLMResponse:
        if not self.client:
            raise RuntimeError("Anthropic client not initialized. Check API key.")
        
        response = await self.client.messages.create(
            model=model,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            raw_response=response.model_dump()
        )
    
    async def embed(self, text: str) -> List[float]:
        # Anthropic doesn't have embedding API, would need separate service
        raise NotImplementedError("Anthropic does not provide embedding API")


class LocalProvider(BaseLLMProvider):
    """Local/LLaMA-compatible API provider"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = "llama2",
        **kwargs
    ) -> LLMResponse:
        import aiohttp
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            ) as resp:
                data = await resp.json()
                
        return LLMResponse(
            content=data["message"]["content"],
            model=model,
            usage={},
            raw_response=data
        )
    
    async def embed(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": text}
            ) as resp:
                data = await resp.json()
                
        return data["embedding"]


# Provider factory
def get_llm_provider(provider: Optional[str] = None) -> BaseLLMProvider:
    """Get LLM provider instance based on configuration"""
    provider = provider or LLM_PROVIDER
    
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "local": LocalProvider
    }
    
    provider_class = providers.get(provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider}")
    
    return provider_class()


# Global provider instance
_llm_provider: Optional[BaseLLMProvider] = None

def get_provider() -> BaseLLMProvider:
    """Get global LLM provider singleton"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = get_llm_provider()
    return _llm_provider
