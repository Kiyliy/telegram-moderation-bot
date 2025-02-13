from abc import ABC, abstractmethod
from typing import List, Union
from src.core.moderation.types.ModerationTypes import ModerationInputContent, ModerationResult

class IModerationProvider(ABC):
    """审核服务提供者接口"""
    
    @abstractmethod
    async def check_content(self, content: ModerationInputContent) -> ModerationResult:
        """审核内容"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供者名称"""
        pass
