# src/core/moderation/manager.py

from typing import List, Union, Optional
from src.core.moderation.types.ModerationTypes import ModerationInputContent, ModerationResult
from src.core.moderation.providers.base import IModerationProvider

class ModerationManager:
    """审核管理器"""
    
    def __init__(self, providers: List[IModerationProvider]):
        self.providers = {p.provider_name: p for p in providers}

    async def check_content(
        self,
        content: ModerationInputContent,
        provider_name: Optional[str] = None
    ) -> ModerationResult:
        """审核内容"""
        if provider_name and provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not found")
            
        provider = self.providers[provider_name] if provider_name else next(iter(self.providers.values()))
        return await provider.check_content(content)