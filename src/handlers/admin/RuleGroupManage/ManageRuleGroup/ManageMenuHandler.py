from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.admin.base import AdminBaseHandler

class ManageMenuHanlder(AdminBaseHandler):
    """规则组管理中心"""
    
    def _get_admin_main_menu(self, rule_id: str) -> InlineKeyboardMarkup:
        """获取管理员主菜单键盘"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("审核设置 🛠", callback_data=f"admin:rg:{rule_id}:mo"),
             InlineKeyboardButton("查看日志 📋", callback_data=f"admin:rg:{rule_id}:logs")],
            [InlineKeyboardButton("用户管理 🧑", callback_data=f"admin:rg:{rule_id}:users"),
             InlineKeyboardButton("群组管理 👥", callback_data=f"admin:rg:{rule_id}:groups")],
            [InlineKeyboardButton("统计信息 📊", callback_data=f"admin:rg:{rule_id}:stats"),
             InlineKeyboardButton("刷新设置 🔄", callback_data=f"admin:rg:{rule_id}:refresh")],
            [InlineKeyboardButton("删除规则组 🗑️", callback_data=f"admin:rg:{rule_id}:delete")],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:list:0")]
        ])
        
    @CallbackRegistry.register(r"^admin:rg:.{16}(:menu)?$")
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组编辑主菜单"""
        query: CallbackQuery = update.callback_query
        rule_id = query.data.split(":")[2]
        if not query or not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 抱歉，您没有管理员权限。")
            return

        await query.edit_message_text(
            f"EditRuleGroupMenu"
            f"👋 欢迎使用规则组控制面板\n"
            f"当前的规则组编号: {rule_id}\n"
            f"请选择以下功能：",
            reply_markup=self._get_admin_main_menu(rule_id)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:refresh$")
    async def handle_refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理刷新设置回调"""
        query = update.callback_query
        rule_id = query.data.split(":")[2]
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 重新加载所有设置
        self._load_settings()
        await query.answer("✅ 设置已刷新")
        
        # 返回主菜单
        await self._safe_edit_message(
            query,
            "👋 欢迎使用规则组控制面板\n"
            f"当前的规则组编号: {rule_id}\n"
            "请选择以下功能：",
            reply_markup=self._get_admin_main_menu(rule_id)
        )

ManageMenuHanlder()