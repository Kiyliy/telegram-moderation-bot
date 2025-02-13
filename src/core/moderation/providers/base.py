from abc import ABC, abstractmethod
from typing import List, Union
from ..models import ModerationInput, ModerationResult

class IModerationProvider(ABC):
    """审核服务提供者接口"""
    
    @abstractmethod
    async def check_content(self, content: Union[ModerationInput, List[ModerationInput]]) -> ModerationResult:
        """审核内容"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供者名称"""
        pass
