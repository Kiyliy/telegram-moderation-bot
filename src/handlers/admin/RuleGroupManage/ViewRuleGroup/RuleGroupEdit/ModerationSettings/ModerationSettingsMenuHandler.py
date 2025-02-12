from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.RuleGroupService import RuleGroupService
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
from typing import Optional

class ModerationSettingsMenuHandler(AdminBaseHandler):
    """规则组管理处理器"""
    
    def __init__(self):
        super().__init__()
        self.rule_group_service = RuleGroupService()
        
    def _get_rule_group_menu(self, rule_group_id: str) -> InlineKeyboardMarkup:
        """获取规则组菜单"""
        keyboard = [
            [
                InlineKeyboardButton("审核规则", callback_data=f"admin:rg:{rule_group_id}:moderation:rules"),
                InlineKeyboardButton("敏感度", callback_data=f"admin:rg:{rule_group_id}:moderation:sensitivity")
            ],
            [
                InlineKeyboardButton("警告消息", callback_data=f"admin:rg:{rule_group_id}:moderation:warning"),
                InlineKeyboardButton("自动处理", callback_data=f"admin:rg:{rule_group_id}:moderation:auto")
            ],
            [
                InlineKeyboardButton("惩罚措施", callback_data=f"admin:rg:{rule_group_id}:moderation:punishment"),
                InlineKeyboardButton("群组管理", callback_data=f"admin:rg:{rule_group_id}:moderation:groups")
            ],
            [InlineKeyboardButton("« 返回规则组列表", callback_data="admin:rule_groups:list")]
        ]
        return InlineKeyboardMarkup(keyboard)
        

# 初始化处理器
ModerationSettingsMenuHandler() 