# src/core/config/config.py
import json
from typing import Any, Dict

class Config:
    """配置管理类"""
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._config:
            self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        config_path = "data/config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except FileNotFoundError:
            print(f"[WARNING] 配置文件不存在: {config_path}")
            self._config = {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] 配置文件格式错误: {e}")
            self._config = {}

    @classmethod
    def get_config(cls, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，格式如 "database.daily_points"
            default: 默认值，当配置不存在时返回

        Returns:
            配置值或默认值

        Example:
            >>> Config.get_config("database.daily_points", 100)
            100
        """
        if cls._instance is None:
            cls._instance = cls()

        # 按照点号分割键
        parts = key.split('.')
        value = cls._instance._config

        # 逐层查找
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

# 创建一个全局实例
config = Config()

# 使用示例:
"""
# config.json 示例:
{
    "database": {
        "daily_points": 100,
        "connection": {
            "host": "localhost",
            "port": 27017
        }
    },
    "bot": {
        "token": "your_bot_token",
        "admin_ids": [123456789]
    }
}

# 使用方式:
from src.core.config.config import config
from src.core.config.ConfigKeys import ConfigKeys as configkey

# 获取配置
daily_points = config.get_config(configkey.database.DAILY_POINTS, 100)
"""