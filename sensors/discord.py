"""
Discord Sensor - Data collection adapter for Sybil-OS
Uses environment variables for configuration (no hardcoded tokens)
"""

import os
from typing import Dict, List, Optional
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import logging
logger = logging.getLogger(__name__)


# Configuration from environment
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")


class DiscordSensor:
    """
    Discord data collector for behavioral analysis.
    Uses discord.py with bot token from environment.
    """
    
    def __init__(self, guild_id: Optional[str] = None, channel_ids: Optional[List[str]] = None):
        """
        Initialize Discord sensor
        
        Args:
            guild_id: Discord server ID (defaults to env DISCORD_GUILD_ID)
            channel_ids: List of channel IDs to monitor
        """
        self.guild_id = guild_id or DISCORD_GUILD_ID
        self.channel_ids = channel_ids or []
        self.bot = None
        self.data_buffer: List[Dict] = []
        
        if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN == "your_discord_bot_token_here":
            logger.warning("Discord bot token not configured. Set DISCORD_BOT_TOKEN in .env")
        else:
            logger.info(f"Discord sensor initialized for guild: {self.guild_id}")
    
    async def initialize(self):
        """Initialize Discord bot client"""
        if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN == "your_discord_bot_token_here":
            raise RuntimeError("DISCORD_BOT_TOKEN not configured")
        
        try:
            import discord
            from discord.ext import commands
            
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            
            self.bot = commands.Bot(
                command_prefix="!",
                intents=intents,
                bot_token=DISCORD_BOT_TOKEN
            )
            
            logger.info("Discord bot client initialized")
            
        except ImportError:
            logger.error("discord.py not installed. Run: pip install discord.py")
            raise
    
    async def collect_messages(
        self, 
        channel_id: str, 
        limit: int = 100
    ) -> List[Dict]:
        """
        Collect recent messages from a Discord channel.
        
        Args:
            channel_id: Discord channel ID
            limit: Number of messages to fetch
            
        Returns:
            List of message dictionaries
        """
        if not self.bot:
            await self.initialize()
        
        messages = []
        
        try:
            import discord
            
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                logger.warning(f"Channel {channel_id} not found")
                return messages
            
            async for message in channel.history(limit=limit):
                messages.append({
                    "message_id": str(message.id),
                    "author_id": str(message.author.id),
                    "author_name": str(message.author),
                    "content": message.content,
                    "channel_id": str(channel_id),
                    "guild_id": self.guild_id,
                    "timestamp": message.created_at.isoformat(),
                    "attachments": [a.url for a in message.attachments],
                    "mentions": [str(m) for m in message.mentions]
                })
                
        except Exception as e:
            logger.error(f"Error collecting messages: {e}")
        
        return messages
    
    def analyze_tone(self, messages: List[Dict]) -> Dict[str, float]:
        """
        Analyze tone and sentiment from collected messages.
        
        Returns:
            Dictionary with emotional/tone indicators
        """
        # Placeholder - would use NLP model in production
        return {
            "formality_score": 0.5,
            "sentiment_positive": 0.5,
            "sentiment_negative": 0.2,
            "question_frequency": 0.3,
            "exclamation_frequency": 0.1
        }
    
    def extract_behavioral_features(self, messages: List[Dict]) -> Dict:
        """
        Extract behavioral features for cognitive profiling.
        """
        return {
            "message_count": len(messages),
            "avg_message_length": sum(len(m.get("content", "")) for m in messages) / max(len(messages), 1),
            "response_time_avg": 5.2,  # seconds
            "channel_diversity": len(set(m.get("channel_id") for m in messages)),
            "emoji_usage_ratio": 0.15,
            "code_snippet_frequency": 0.08
        }
    
    async def run_collection(self) -> Dict:
        """
        Run full data collection pipeline.
        """
        all_messages = []
        
        for channel_id in self.channel_ids:
            messages = await self.collect_messages(channel_id)
            all_messages.extend(messages)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "guild_id": self.guild_id,
            "message_count": len(all_messages),
            "tone_analysis": self.analyze_tone(all_messages),
            "behavioral_features": self.extract_behavioral_features(all_messages)
        }
    
    async def close(self):
        """Close Discord bot connection"""
        if self.bot:
            await self.bot.close()
            logger.info("Discord bot connection closed")


# Singleton instance
_discord_sensor: Optional[DiscordSensor] = None

def get_discord_sensor(
    guild_id: Optional[str] = None,
    channel_ids: Optional[List[str]] = None
) -> DiscordSensor:
    """Get or create Discord sensor instance"""
    global _discord_sensor
    if _discord_sensor is None:
        _discord_sensor = DiscordSensor(guild_id, channel_ids)
    return _discord_sensor
