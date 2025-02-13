# src/core/moderation/types/CategoryTypes.py
from enum import Enum
from typing import Dict, TypedDict

class OpenAIModerationCategory(str, Enum):
    """OpenAI支持的审核类别"""
    SEXUAL = "sexual"
    SEXUAL_MINORS = "sexual/minors"
    HARASSMENT = "harassment"
    HARASSMENT_THREATENING = "harassment/threatening"
    HATE = "hate"
    HATE_THREATENING = "hate/threatening"
    ILLICIT = "illicit"
    ILLICIT_VIOLENT = "illicit/violent"
    SELF_HARM = "self-harm"
    SELF_HARM_INTENT = "self-harm/intent"
    SELF_HARM_INSTRUCTIONS = "self-harm/instructions"
    VIOLENCE = "violence"
    VIOLENCE_GRAPHIC = "violence/graphic"

class OpenAISettings(TypedDict):
    """OpenAI审核设置类型"""
    categories: Dict[str, bool]  # 是否启用该类别
    sensitivity: Dict[str, float]  # 敏感度阈值