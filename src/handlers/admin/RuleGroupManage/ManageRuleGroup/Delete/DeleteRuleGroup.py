from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.RuleGroupService import RuleGroupService

class DeleteRuleGroupHandler(AdminBaseHandler):
    """规则组管理中心"""
    
    def __init__(self):
        super().__init__()
        self.rule_group_service = RuleGroupService()
    
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:delete(:confirm)?$")
    async def handle_delete_rule_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理删除规则组回调"""
        query = update.callback_query
        rule_id = query.data.split(":")[2]
        
        # 检查是否是管理员
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 先显示确认键盘的按钮
        if not query.data.endswith(":confirm"):
            await query.edit_message_text(
                "⚠️ 请确认删除规则组",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚠️ 确认删除", callback_data=f"admin:rg:{rule_id}:delete:confirm")]
                ])
            )
            return
        else:
            # 删除规则组
            await self.rule_group_service.delete_rule_group(rule_id)
            await query.answer("✅ 规则组已删除")
            await query.edit_message_text(
                "✅ 规则组已删除",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:list:0")]
                ])
            )

DeleteRuleGroupHandler()