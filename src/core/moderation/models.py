from typing import Dict, List, Optional, Union, Any
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl

class ContentType(str, Enum):
    """内容类型"""
    TEXT = "text"
    IMAGE_URL = "image_url"
    VIDEO = "video"  # 预留扩展


class ModerationInputContent(BaseModel):
    """审核输入内容"""
    type: ContentType
    text: Optional[str] = None
    image_urls: Optional[List[str]] = None
    extra: Dict[str, Any] = Field(default_factory=dict)  # 额外参数

class ModerationCategory(BaseModel):
    """审核类别结果"""
    flagged: bool
    score: float
    applied_input_types: List[str]  # 记录是基于哪些输入类型做出的判断
    details: Optional[Dict[str, Any]] = None

class ModerationResult(BaseModel):
    """单条审核结果"""
    flagged: bool
    provider: str
    categories: Dict[str, ModerationCategory]
    category_scores: Dict[str, float]  # OpenAI 的分数字段
    category_applied_input_types: Dict[str, List[str]]  # OpenAI 的输入类型应用字段

class ModerationResponse(BaseModel):
    """完整的审核响应"""
    id: str
    model: str
    results: List[ModerationResult]
    raw_response: Dict[str, Any]

class BaseProvider:
    """审核提供者基类"""
    name: str = "base"  # 提供者标识
    
    async def check_contents(
        self, 
        inputs: List[ModerationInputContent]
    ) -> ModerationResponse:
        """批量审核内容"""
        raise NotImplementedError
        
    async def check_content(
        self, 
        content: Union[str, HttpUrl], 
        type: ContentType = ContentType.TEXT
    ) -> ModerationResponse:
        """单条审核(便捷方法)"""
        input_content = ModerationInputContent(
            type=type,
            text=content if type == ContentType.TEXT else None,
            image_urls=[content] if type == ContentType.IMAGE_URL else None
        )
        return await self.check_contents([input_content]) 