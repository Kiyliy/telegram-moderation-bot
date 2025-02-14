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
    video: Optional[str] = None
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
    provider: str = "openai"
    raw_response: Optional[Dict[str, Any]] = {}
    categories: Optional[Dict[str, bool]] = {}
    category_scores: Optional[Dict[str, float]] = {}
    category_applied_input_types: Optional[List[str]] = []

class ModerationResponse(BaseModel):
    """完整的审核响应"""
    id: str
    model: str
    results: List[ModerationResult]
    raw_response: Dict[str, Any]

