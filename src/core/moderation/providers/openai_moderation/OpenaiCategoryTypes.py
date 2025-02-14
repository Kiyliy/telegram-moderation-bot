from enum import Enum
from typing import Dict, TypedDict, Optional, Union

class OpenAIModerationCategory(str, Enum):
    """OpenAI支持的审核类别"""
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

    @classmethod
    def validate_category(cls, category: str) -> bool:
        """验证类别是否有效"""
        return category in [e.value for e in cls]

    @classmethod
    def from_str(cls, category: str) -> Optional['OpenAIModerationCategory']:
        """从字符串转换为枚举值"""
        try:
            return cls(category)
        except ValueError:
            return None

class OpenAISettingsType(TypedDict):
    """OpenAI审核设置"""
    categories: Dict[str, bool]  # 每个类别是否启用
    sensitivity: Dict[str, float]  # 每个类别的敏感度阈值

    @classmethod
    def validate_config(cls, config: Dict) -> bool:
        """验证配置是否有效"""
        if not isinstance(config, dict):
            return False
            
        required_keys = {'categories', 'sensitivity'}
        if not all(key in config for key in required_keys):
            return False

        # 验证所有类别是否有效
        for category in config['categories'].keys():
            if not OpenAIModerationCategory.validate_category(category):
                return False

        # 验证敏感度值是否在有效范围内
        for value in config['sensitivity'].values():
            if not isinstance(value, (int, float)) or value < 0 or value > 1:
                return False

        return True

    @classmethod
    def from_dict(cls, config: Dict) -> Optional['OpenAISettingsType']:
        """从字典转换为设置对象"""
        if not cls.validate_config(config):
            return None
        return cls(
            categories=config['categories'],
            sensitivity=config['sensitivity']
        )
