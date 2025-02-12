from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler


class AdminGroupMenuHandler(AdminBaseHandler):
    """群组管理菜单处理器"""
    
    def __init__(self):
        super().__init__()

    @CallbackRegistry.register(r"^admin:groups$")
    async def handle_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理群组管理入口"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton("群组列表", callback_data="admin:groups:list:1")],
            [InlineKeyboardButton("« 返回", callback_data="admin:back")]
        ]

        await self._safe_edit_message(
            query,
            "👥 群组管理\n"
            "请选择要进行的操作：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# 初始化处理器
AdminGroupMenuHandler() 