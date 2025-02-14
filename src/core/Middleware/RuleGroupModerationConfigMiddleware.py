from typing import List, Optional
from src.core.moderation.providers.base import IModerationProvider
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
from src.core.moderation.types.CategoryTypes import CategorySettings
from src.core.moderation.manager import ModerationManager
from src.core.moderation.providers.openai_moderation.openai_provider import OpenAIModerationProvider
from src.core.moderation.config import ModerationConfig
from src.core.moderation.types.ModerationTypes import ModerationInputContent, ModerationResult

class RuleGroupModerationConfigMiddleware(ModerationManager):
    """从 rule_group_config 获取审核配置的中间件"""
    
    def __init__(self):
        providers = [
            OpenAIModerationProvider()
        ]
        super().__init__(providers=providers)
        
    @staticmethod
    async def get_moderation_config(rule_group_id: str) -> tuple[str, CategorySettings]:
        """
        获取规则组的审核配置
        
        Args:
            rule_group_id: 规则组ID
            
        Returns:
            tuple[str, CategorySettings]: (provider名称, provider的分类配置)
        """
        # 获取当前provider
        current_provider = await rule_group_config.get_config(
            rule_group_id,
            configkey.moderation.ACTIVE_PROVIDER
        ) or "openai"
        
        # 获取provider的配置
        provider_configs = await rule_group_config.get_config(
            rule_group_id,
            getattr(configkey.moderation.providers, current_provider.lower())
        )
        
        return current_provider, provider_configs
    
    async def check_content(
        self,
        rule_group_id: str,
        content: ModerationInputContent
    ) -> ModerationResult:
        # 如果rule_group_id为空, 则使用默认的provider
        if not rule_group_id:
            return super().check_content(content, "openai", None)
        current_provider, provider_configs = await self.get_moderation_config(rule_group_id)
        return super().check_content(content, current_provider, provider_configs)
    
