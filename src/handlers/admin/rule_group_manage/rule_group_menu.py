from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.RuleGroupService import RuleGroupService
from src.core.database.service.chatsService import ChatService

# 会话状态
WAITING_NAME = 1
WAITING_DESCRIPTION = 2

class RuleGroupMenuHandler(AdminBaseHandler):
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

    @CallbackRegistry.register(r"^admin:rule_group:create$")
    async def handle_create_rule_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理创建规则组"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        await query.answer()
        # 存储用户ID
        context.user_data['creating_rule_group'] = True
        
        await query.edit_message_text(
            "✏️ 请输入规则组名称：\n"
            "（发送 /cancel 取消创建）"
        )
        return WAITING_NAME

    @MessageRegistry.register(MessageFilters.text & ~MessageFilters.command)
    async def handle_rule_group_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组名称输入"""
        if not context.user_data.get('creating_rule_group'):
            return
            
        name = update.message.text
        if len(name) > 50:
            await update.message.reply_text(
                "❌ 规则组名称过长，请不要超过50个字符\n"
                "请重新输入："
            )
            return WAITING_NAME
            
        # 存储名称
        context.user_data['rule_group_name'] = name
        
        await update.message.reply_text(
            "✏️ 请输入规则组描述：\n"
            "（发送 /skip 跳过，/cancel 取消）"
        )
        return WAITING_DESCRIPTION

    @MessageRegistry.register(MessageFilters.text & ~MessageFilters.command)
    async def handle_rule_group_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组描述输入"""
        if not context.user_data.get('creating_rule_group'):
            return
            
        description = update.message.text
        name = context.user_data.get('rule_group_name')
        
        # 创建规则组
        rule_group = await self.rule_group_service.create_rule_group(
            name=name,
            owner_id=update.effective_user.id,
            description=description
        )
        
        if rule_group:
            await update.message.reply_text(
                f"✅ 规则组「{name}」创建成功！\n"
                f"ID: {rule_group.id}\n"
                f"描述: {description}\n\n"
                "现在您可以：\n"
                "1. 绑定群组到此规则组\n"
                "2. 配置规则组的审核设置\n"
                "3. 查看规则组统计信息",
                reply_markup=self._get_rule_group_menu()
            )
        else:
            await update.message.reply_text(
                "❌ 创建失败，请重试",
                reply_markup=self._get_rule_group_menu()
            )
            
        # 清理上下文
        context.user_data.clear()
        return ConversationHandler.END

    @MessageRegistry.register(MessageFilters.command & MessageFilters.match_command(['skip']))
    async def handle_skip_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理跳过描述"""
        if not context.user_data.get('creating_rule_group'):
            return
            
        name = context.user_data.get('rule_group_name')
        
        # 创建规则组
        rule_group = await self.rule_group_service.create_rule_group(
            name=name,
            owner_id=update.effective_user.id
        )
        
        if rule_group:
            await update.message.reply_text(
                f"✅ 规则组「{name}」创建成功！\n"
                f"ID: {rule_group.id}\n\n"
                "现在您可以：\n"
                "1. 绑定群组到此规则组\n"
                "2. 配置规则组的审核设置\n"
                "3. 查看规则组统计信息",
                reply_markup=self._get_rule_group_menu()
            )
        else:
            await update.message.reply_text(
                "❌ 创建失败，请重试",
                reply_markup=self._get_rule_group_menu()
            )
            
        # 清理上下文
        context.user_data.clear()
        return ConversationHandler.END

    @MessageRegistry.register(MessageFilters.command & MessageFilters.match_command(['cancel']))
    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理取消创建"""
        if not context.user_data.get('creating_rule_group'):
            return
            
        await update.message.reply_text(
            "❌ 已取消创建规则组",
            reply_markup=self._get_rule_group_menu()
        )
        
        # 清理上下文
        context.user_data.clear()
        return ConversationHandler.END

    @CallbackRegistry.register(r"^admin:rule_group:list(?::(\d+))?$")
    async def handle_list_rule_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理查看规则组列表"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 获取页码
        page = int(query.data.split(":")[-1]) if ":" in query.data else 0
        
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

# 初始化处理器
RuleGroupMenuHandler() 