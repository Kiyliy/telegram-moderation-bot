from typing import Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

class ContentType(str, Enum):
    """内容类型"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"

class ModerationInput(BaseModel):
    """审核输入"""
    type: ContentType
    content: Union[str, List[str]]  # 文本内容或URL列表
    extra: Dict = Field(default_factory=dict)  # 额外参数

class ModerationCategory(BaseModel):
    """审核类别结果"""
    flagged: bool
    score: float
    details: Optional[Dict] = None

class ModerationResult(BaseModel):
    """审核结果"""
    flagged: bool
    categories: Dict[str, ModerationCategory]
    provider: str
    raw_response: Dict
    input_type: ContentType
    input_content: Union[str, List[str]]
