from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.handlers.admin.base import AdminBaseHandler
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.MessageFilters import MessageFilters

class AdminMenuHandler(AdminBaseHandler):
    def __init__(self):
        super().__init__()

    def get_admin_menu_keyboard(self) -> InlineKeyboardMarkup:
        """获取管理员主菜单键盘"""
        keyboard = [
            [InlineKeyboardButton("📋 规则组管理", callback_data="admin:rule_group")],
            [InlineKeyboardButton("👥 群组管理", callback_data="admin:group")],
            [InlineKeyboardButton("⚖️ 审核管理", callback_data="admin:moderation")],
            [InlineKeyboardButton("📊 统计信息", callback_data="admin:stats")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @MessageRegistry.register(MessageFilters.match_regex('^/?admin$'))
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理/admin命令"""
        if not self._is_admin(update.effective_user.id):
            return
            
        print("aaaaaaaaaaaa")
        await update.message.reply_text(
            "👋 欢迎使用管理员控制面板\n"
            "请选择要进行的操作:",
            reply_markup=self.get_admin_menu_keyboard()
        )

AdminMenuHandler()