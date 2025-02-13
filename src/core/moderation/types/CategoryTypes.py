# src/core/moderation/types/CategoryTypes.py
from enum import Enum
from typing import Dict, TypedDict

class ModerationCategory(str, Enum):
    """审核类别"""
    pass

class CategorySettings(TypedDict):
    """审核设置"""
    categories: Dict[str, bool]  # 是否启用该类别
    sensitivity: Dict[str, float]  # 敏感度阈值