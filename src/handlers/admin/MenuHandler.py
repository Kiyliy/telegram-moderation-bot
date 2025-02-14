from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.handlers.admin.base import AdminBaseHandler
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.core.registry.CallbackRegistry import CallbackRegistry

class MenuHandler(AdminBaseHandler):
    def __init__(self):
        super().__init__()

    def get_admin_menu_keyboard(self) -> InlineKeyboardMarkup:
        """获取管理员主菜单键盘"""
        keyboard = [
            [InlineKeyboardButton("📋 规则组管理", callback_data="admin:rg:list")],
            [InlineKeyboardButton("👥 群组管理", callback_data="admin:group")],
            [InlineKeyboardButton("⚖️ 审核管理", callback_data="admin:mo")],
            [InlineKeyboardButton("📊 统计信息", callback_data="admin:stats")]
        ]
        return InlineKeyboardMarkup(keyboard)


    @MessageRegistry.register(MessageFilters.match_regex(r'^/?admin$'))
    @CallbackRegistry.register(r"^admin$")
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理/admin命令"""
        if not self._is_admin(update.effective_user.id):
            return
        
        call_type = "callback" if update.callback_query else "msg"
        if call_type == "msg":
            await update.message.reply_text(
                "👋 欢迎使用管理员控制面板\n"
                "请选择要进行的操作:",
                reply_markup=self.get_admin_menu_keyboard()
            )
        else:
            await update.callback_query.edit_message_text(
                "👋 欢迎使用管理员控制面板\n"
                "请选择要进行的操作:",
                reply_markup=self.get_admin_menu_keyboard()
            )

MenuHandler()