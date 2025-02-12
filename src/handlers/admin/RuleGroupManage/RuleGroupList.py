from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.RuleGroupService import RuleGroupService
from src.core.database.service.chatsService import ChatService


class RuleGroupListHandler(AdminBaseHandler):
    """规则组管理菜单处理器"""
    
    def __init__(self):
        super().__init__()
        self.rule_group_service = RuleGroupService()
        self.chat_service = ChatService()
        
    def _get_rule_group_menu(self) -> InlineKeyboardMarkup:
        """获取规则组管理菜单键盘"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("创建规则组 ➕", callback_data="admin:rule_group:create")],
            [InlineKeyboardButton("查看规则组 📋", callback_data="admin:rule_group:list")],
            [InlineKeyboardButton("« 返回", callback_data="admin:back")]
        ])

    def _get_rule_group_list_keyboard(self, rule_groups: list, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
        """获取规则组列表键盘"""
        total_pages = (len(rule_groups) + per_page - 1) // per_page
        start = page * per_page
        end = start + per_page
        
        keyboard = []
        # 添加规则组按钮
        for rule_group in rule_groups[start:end]:
            keyboard.append([
                InlineKeyboardButton(
                    f"📋 {rule_group.name}",
                    callback_data=f"admin:rule_group:view:{rule_group.id}"
                )
            ])
            
        # 添加翻页按钮
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("⬅️", callback_data=f"admin:rule_group:list:{page-1}")
            )
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton("➡️", callback_data=f"admin:rule_group:list:{page+1}")
            )
        if nav_buttons:
            keyboard.append(nav_buttons)
            
        # 添加返回按钮
        keyboard.append([InlineKeyboardButton("« 返回", callback_data="admin:rule_group")])
        
        return InlineKeyboardMarkup(keyboard)

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
