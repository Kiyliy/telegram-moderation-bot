from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.RuleGroupService import RuleGroupService
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
from typing import Optional

class ModerationMenuHandler(AdminBaseHandler):
    """规则组管理处理器"""
    
    def __init__(self):
        super().__init__()
        self.rule_group_service = RuleGroupService()
    
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo(:menu)?$")
    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理审核设置回调"""
        query = update.callback_query
        rule_id = query.data.split(":")[2]
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton("审核规则设置", callback_data=f"admin:rg:{rule_id}:mo:rules"),
             InlineKeyboardButton("敏感度设置", callback_data=f"admin:rg:{rule_id}:mo:sen")],
            [InlineKeyboardButton("警告消息设置", callback_data=f"admin:rg:{rule_id}:mo:warning"),
             InlineKeyboardButton("自动处理设置", callback_data=f"admin:rg:{rule_id}:mo:auto")],
            [InlineKeyboardButton("惩罚措施设置", callback_data=f"admin:rg:{rule_id}:mo:punishment")],
            [InlineKeyboardButton("Provider选择", callback_data=f"admin:rg:{rule_id}:mo:provider:list")],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_id}")]
        ]

        await self._safe_edit_message(
            query,
            "⚙️ 审核设置\n"
            "请选择要修改的设置项：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# 初始化处理器
ModerationMenuHandler() 