from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler


class SelectActionHandler(AdminBaseHandler):
    """规则组管理菜单处理器"""
    
    def __init__(self):
        super().__init__()
        
    @classmethod
    def _get_rule_group_menu(cls) -> InlineKeyboardMarkup:
        """获取规则组管理菜单键盘"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("创建规则组 ➕", callback_data="admin:rule_group:create")],
            [InlineKeyboardButton("查看规则组 📋", callback_data="admin:rule_group:list")],
            [InlineKeyboardButton("« 返回", callback_data="admin:back")]
        ])
        
    @CallbackRegistry.register(r"^admin:rule_group$")
    async def handle_rule_group_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组管理菜单"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        await self._safe_edit_message(
            query,
            "📋 规则组管理\n"
            "请选择操作：",
            reply_markup=self._get_rule_group_menu()
        )
    
SelectActionHandler()