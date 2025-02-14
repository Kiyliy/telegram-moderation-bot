from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.RuleGroupService import RuleGroupService
from src.core.database.service.chatsService import ChatService
from src.core.database.models.db_rule_group import RuleGroup

# class RuleGroupListLayout:
#     """规则组列表布局"""
#     InlineKeyboardButton("<<GroupList>>", callback_data="admin:rg:.{16}(:menu)?")
#     InlineKeyboardButton("创建规则组 ➕", callback_data="admin:rg:create")
#     InlineKeyboardButton("查看规则组 📋", callback_data="admin:rg:list")
#     InlineKeyboardButton("« 返回", callback_data="admin")


class RuleGroupListHandler(AdminBaseHandler):
    """规则组管理菜单处理器"""
    
    def __init__(self):
        super().__init__()
        self.rule_group_service = RuleGroupService()
        self.chat_service = ChatService()
        
    @classmethod
    def _get_rule_group_menu(cls) -> InlineKeyboardMarkup:
        """获取规则组管理菜单键盘"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("创建规则组 ➕", callback_data="admin:rg:create")],
            [InlineKeyboardButton("查看规则组 📋", callback_data="admin:rg:list")],
            [InlineKeyboardButton("« 返回", callback_data="admin")]
        ])
        
    # @CallbackRegistry.register(r"^admin:rg$")
    # async def handle_rule_group_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """处理规则组管理菜单"""
    #     query = update.callback_query
    #     if not self._is_admin(query.from_user.id):
    #         await query.answer("⚠️ 没有权限", show_alert=True)
    #         return

    #     await self._safe_edit_message(
    #         query,
    #         "📋 规则组管理\n"
    #         "请选择操作：",
    #         reply_markup=self._get_rule_group_menu()
    #     )

    def _get_rule_group_list_keyboard(self, rule_groups: RuleGroup, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
        """获取规则组列表键盘"""
        total_pages = (len(rule_groups) + per_page - 1) // per_page
        start = page * per_page
        end = start + per_page
        
        keyboard = []
        # 添加规则组按钮

        for rule_group in rule_groups[start:end]:
            rule_group: RuleGroup
            keyboard.append([
                InlineKeyboardButton(
                    f"📋 {rule_group.name}",
                    callback_data=f"admin:rg:{rule_group.rule_id}"
                )
            ])
            
        # 添加翻页按钮
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("⬅️", callback_data=f"admin:rg:list:{page-1}")
            )
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton("➡️", callback_data=f"admin:rg:list:{page+1}")
            )
        if nav_buttons:
            keyboard.append(nav_buttons)
            
        # 添加返回按钮
        keyboard.append([InlineKeyboardButton("创建规则组 ➕", callback_data="admin:rg:create")])
        keyboard.append(
            [InlineKeyboardButton("« 返回", callback_data="admin"),
             InlineKeyboardButton("🔄 刷新", callback_data="admin:rg:list")])
        
        return InlineKeyboardMarkup(keyboard)


    @CallbackRegistry.register(r"^admin:rg:list?(?::(\d+))?$")
    async def handle_list_rule_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理查看规则组列表"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 获取页码
        page = int(query.data.split(":")[-1]) if type(query.data.split(":")[-1]) == int else 0
        
        # 获取规则组列表
        rule_groups = await self.rule_group_service.get_owner_rule_groups(query.from_user.id)
        
        if not rule_groups:
            await query.answer("还没有创建任何规则组")
            await self._safe_edit_message(
                query,
                "📋 规则组列表为空\n"
                "点击「创建规则组」来创建第一个规则组",
                reply_markup=self._get_rule_group_menu()
            )
            return
            
        # 构建消息
        text = "📋 规则组列表\n\n"
        keyboard = self._get_rule_group_list_keyboard(rule_groups, page)
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=keyboard
        )

RuleGroupListHandler()