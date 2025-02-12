from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.RuleGroupService import RuleGroupService
from src.core.database.service.chatsService import ChatService

class CreateRuleGroupHandler(AdminBaseHandler):
    
    def __init__(self):
        super().__init__()
        self.rule_group_service = RuleGroupService()
        
    @CallbackRegistry.register(r"^admin:rule_group:create$")
    async def handle_create_rule_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理创建规则组"""
        query: CallbackQuery = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        await query.answer()
        await query.edit_message_text(
            "✏️ 请输入规则组名称：\n"
            "（回复此消息输入名称，发送 /cancel 取消创建）",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("取消", callback_data="admin:rule_group:create:cancel")
            ]])
        )

    @MessageRegistry.register(MessageFilters.match_reply_msg_regex(r".*请输入规则组名称.*"))
    async def handle_rule_group_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组名称输入"""
        name = update.message.text
        if len(name) > 50:
            await update.message.reply_text(
                "❌ 规则组名称过长，请不要超过50个字符\n"
                "请重新输入名称："
            )
            return
            
        # 请求输入描述
        await update.message.reply_text(
            f"规则组名称: {name}\n\n"
            "✏️ 请输入规则组描述：\n"
            "（回复此消息输入描述，发送 /skip 跳过）",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("跳过", callback_data=f"admin:rule_group:create:skip:{name}")
            ]])
        )

    @MessageRegistry.register(MessageFilters.match_reply_msg_regex(r".*请输入规则组描述.*"))
    async def handle_rule_group_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组描述输入"""
        description = update.message.text
        # 从回复的消息中提取名称
        name = update.message.reply_to_message.text.split("规则组名称: ")[1].split("\n")[0]
        
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
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("配置规则组", callback_data=f"admin:rule_group:edit:{rule_group.id}")
                ]])
            )
        else:
            await update.message.reply_text(
                "❌ 创建失败，请重试",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("返回", callback_data="admin:rule_group")
                ]])
            )

    @CallbackRegistry.register(r"^admin:rule_group:create:skip:(.+)$")
    async def handle_skip_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理跳过描述"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        name = query.data.split(":")[-1]
        
        # 创建规则组
        rule_group = await self.rule_group_service.create_rule_group(
            name=name,
            owner_id=query.from_user.id
        )
        
        if rule_group:
            await query.edit_message_text(
                f"✅ 规则组「{name}」创建成功！\n"
                f"ID: {rule_group.id}\n\n"
                "现在您可以：\n"
                "1. 绑定群组到此规则组\n"
                "2. 配置规则组的审核设置\n"
                "3. 查看规则组统计信息",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("配置规则组", callback_data=f"admin:rule_group:edit:{rule_group.id}")
                ]])
            )
        else:
            await query.edit_message_text(
                "❌ 创建失败，请重试",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("返回", callback_data="admin:rule_group")
                ]])
            )

    @CallbackRegistry.register(r"^admin:rule_group:create:cancel$")
    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理取消创建"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        await query.edit_message_text(
            "❌ 已取消创建规则组",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("返回", callback_data="admin:rule_group")
            ]])
        )



# 初始化处理器
CreateRuleGroupHandler() 