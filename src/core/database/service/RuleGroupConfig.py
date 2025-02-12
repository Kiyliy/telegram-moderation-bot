import json
from typing import Dict, Any, Optional
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
from src.core.database.db.RuleGroupDatabase import RuleGroupDatabase


class RuleGroupConfig:
    """规则组配置管理类"""
    _instance = None
    _config_cache: Dict[str, Dict] = {}  # rule_group_id -> config
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
        
    def _init(self):
        """初始化"""
        self.rule_group_db = RuleGroupDatabase()
        self._load_default_config()
        
    def _load_default_config(self) -> None:
        """加载默认配置"""
        try:
            with open("src/core/database/service/default_config.json", "r", encoding="utf-8") as f:
                self._default_config = json.load(f)
        except Exception as e:
            print(f"[ERROR] 加载默认配置失败: {e}")
            self._default_config = {}
            
    def _get_nested_value(self, config: Dict, key: str, default: Any = None) -> Any:
        """获取嵌套字典中的值"""
        parts = key.split(".")
        value = config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
                
        return value
        
    def _set_nested_value(self, config: Dict, key: str, value: Any) -> None:
        """设置嵌套字典中的值"""
        parts = key.split(".")
        current = config
        
        # 创建嵌套结构
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        # 设置最终值
        current[parts[-1]] = value
        
    async def get_config(self, rule_group_id: str, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            rule_group_id: 规则组ID
            key: 配置键，如 "moderation.rules.nsfw"
            default: 默认值
        """
        # 尝试从缓存获取
        if rule_group_id not in self._config_cache:
            # 从数据库加载
            settings = await self.rule_group_db.get_rule_group_settings(rule_group_id)
            if settings:
                self._config_cache[rule_group_id] = settings
            else:
                # 使用默认配置
                self._config_cache[rule_group_id] = self._default_config.copy()
                
        return self._get_nested_value(
            self._config_cache[rule_group_id],
            key,
            self._get_nested_value(self._default_config, key, default)
        )
        
    async def set_config(self, rule_group_id: str, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            rule_group_id: 规则组ID
            key: 配置键，如 "moderation.rules.nsfw"
            value: 要设置的值
        """
        # 确保配置已加载
        if rule_group_id not in self._config_cache:
            settings = await self.rule_group_db.get_rule_group_settings(rule_group_id)
            self._config_cache[rule_group_id] = settings or self._default_config.copy()
            
        # 更新配置
        self._set_nested_value(self._config_cache[rule_group_id], key, value)
        
        # 保存到数据库
        result = await self.rule_group_db.update_rule_group(
            rule_id=rule_group_id,
            settings=self._config_cache[rule_group_id]
        )
        
        return bool(result)
        
    def clear_cache(self, rule_group_id: Optional[str] = None):
        """
        清除配置缓存
        
        Args:
            rule_group_id: 要清除的规则组ID，如果为None则清除所有缓存
        """
        if rule_group_id:
            self._config_cache.pop(rule_group_id, None)
        else:
            self._config_cache.clear()
            
    async def get_all_config(self, rule_group_id: str) -> Dict:
        """获取规则组的所有配置"""
        if rule_group_id not in self._config_cache:
            settings = await self.rule_group_db.get_rule_group_settings(rule_group_id)
            if settings:
                self._config_cache[rule_group_id] = settings
            else:
                self._config_cache[rule_group_id] = self._default_config.copy()
                
        return self._config_cache[rule_group_id]
        
    async def reset_config(self, rule_group_id: str) -> bool:
        """重置规则组配置为默认值"""
        self._config_cache[rule_group_id] = self._default_config.copy()
        result = await self.rule_group_db.update_rule_group(
            rule_id=rule_group_id,
            settings=self._default_config
        )
        return bool(result)


# 创建全局实例
rule_group_config = RuleGroupConfig() 