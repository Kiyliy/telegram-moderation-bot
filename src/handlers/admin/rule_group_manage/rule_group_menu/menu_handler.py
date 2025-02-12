from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.admin.base import AdminBaseHandler

class AdminMenuHandler(AdminBaseHandler):
    """管理员主菜单处理器"""
    
    def _get_admin_main_menu(self) -> InlineKeyboardMarkup:
        """获取管理员主菜单键盘"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("审核设置 🛠", callback_data="admin:settings"),
             InlineKeyboardButton("查看日志 📋", callback_data="admin:logs")],
            [InlineKeyboardButton("用户管理 🧑", callback_data="admin:users"),
             InlineKeyboardButton("群组管理 👥", callback_data="admin:groups")],
            [InlineKeyboardButton("统计信息 📊", callback_data="admin:stats"),
             InlineKeyboardButton("刷新设置 🔄", callback_data="admin:refresh")]
        ])

    @MessageRegistry.register(MessageFilters.match_prefix(['/admin']))
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /admin 命令"""
        if not update.effective_user or not self._is_admin(update.effective_user.id):
            await update.message.reply_text("⚠️ 抱歉，您没有管理员权限。")
            return

        await update.message.reply_text(
            "👋 欢迎使用管理员控制面板\n"
            "请选择以下功能：",
            reply_markup=self._get_admin_main_menu()
        )

    @CallbackRegistry.register(r"^admin:settings$")
    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理审核设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton("审核规则设置", callback_data="admin:settings:rules"),
             InlineKeyboardButton("敏感度设置", callback_data="admin:settings:sensitivity")],
            [InlineKeyboardButton("警告消息设置", callback_data="admin:settings:warning"),
             InlineKeyboardButton("自动处理设置", callback_data="admin:settings:auto")],
            [InlineKeyboardButton("惩罚措施设置", callback_data="admin:settings:punishment")],
            [InlineKeyboardButton("« 返回", callback_data="admin:back")]
        ]

        await self._safe_edit_message(
            query,
            "⚙️ 审核设置\n"
            "请选择要修改的设置项：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:refresh$")
    async def handle_refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理刷新设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 重新加载所有设置
        self._load_settings()
        await query.answer("✅ 设置已刷新")
        
        # 返回主菜单
        await self._safe_edit_message(
            query,
            "👋 欢迎使用管理员控制面板\n"
            "请选择以下功能：",
            reply_markup=self._get_admin_main_menu()
        )

    @CallbackRegistry.register(r"^admin:back$")
    async def handle_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理返回主菜单回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        await self._safe_edit_message(
            query,
            "👋 欢迎使用管理员控制面板\n"
            "请选择以下功能：",
            reply_markup=self._get_admin_main_menu()
        )

# 初始化处理器
AdminMenuHandler() 