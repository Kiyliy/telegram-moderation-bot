from typing import List, Dict, Union, Any
from pydantic import BaseModel

class ModerationInput:
    """审核输入对象"""
    def __init__(self, content: Union[str, bytes], type: str = "text"):
        self.content = content
        self.type = type  # "text", "image", "audio" 等

class ModerationResult(BaseModel):
    """单条审核结果"""
    flagged: bool
    categories: Dict[str, bool]
    category_scores: Dict[str, float]
    content: Union[str, bytes]
    content_type: str

class ModerationResponse(BaseModel):
    """完整的审核响应"""
    id: str
    results: List[ModerationResult]
    raw_response: Dict[str, Any]

class BaseProvider:
    """审核提供者基类"""
    async def check_contents(
        self, 
        inputs: List[ModerationInput]
    ) -> ModerationResponse:
        """批量审核内容"""
        raise NotImplementedError
        
    async def check_content(
        self, 
        content: Union[str, bytes], 
        type: str = "text"
    ) -> ModerationResponse:
        """单条审核(便捷方法)"""
        return await self.check_contents([ModerationInput(content, type)]) 