from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.RuleGroupService import RuleGroupService
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
from typing import Optional

class AdminRuleGroupHandler(AdminBaseHandler):
    """规则组管理处理器"""
    
    def __init__(self):
        super().__init__()
        self.rule_group_service = RuleGroupService()
        
    def _get_rule_group_menu(self, rule_group_id: str) -> InlineKeyboardMarkup:
        """获取规则组菜单"""
        keyboard = [
            [
                InlineKeyboardButton("审核规则", callback_data=f"admin:settings:rules:{rule_group_id}"),
                InlineKeyboardButton("敏感度", callback_data=f"admin:settings:sensitivity:{rule_group_id}")
            ],
            [
                InlineKeyboardButton("警告消息", callback_data=f"admin:settings:warning:{rule_group_id}"),
                InlineKeyboardButton("自动处理", callback_data=f"admin:settings:auto:{rule_group_id}")
            ],
            [
                InlineKeyboardButton("惩罚措施", callback_data=f"admin:settings:punishment:{rule_group_id}"),
                InlineKeyboardButton("群组管理", callback_data=f"admin:settings:groups:{rule_group_id}")
            ],
            [InlineKeyboardButton("« 返回规则组列表", callback_data="admin:rule_groups:list")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:rule_groups:list$")
    async def handle_rule_groups_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组列表"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        # 获取用户的规则组
        rule_groups = await self.rule_group_service.get_owner_rule_groups(query.from_user.id)
        
        keyboard = []
        if rule_groups:
            for group in rule_groups:
                keyboard.append([
                    InlineKeyboardButton(
                        f"📋 {group.name}",
                        callback_data=f"admin:rule_groups:select:{group.rule_id}"
                    )
                ])
                
        # 添加创建按钮
        keyboard.append([
            InlineKeyboardButton("➕ 创建规则组", callback_data="admin:rule_groups:create")
        ])
        # 返回主菜单
        keyboard.append([
            InlineKeyboardButton("« 返回", callback_data="admin:back")
        ])
        
        await self._safe_edit_message(
            query,
            "📋 规则组列表\n"
            "请选择要管理的规则组，或创建新的规则组：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    @CallbackRegistry.register(r"^admin:rule_groups:select:(\w+)$")
    async def handle_rule_group_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组选择"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[-1]
        
        # 获取规则组信息
        rule_group = await self.rule_group_service.get_rule_group(rule_group_id)
        if not rule_group:
            await query.answer("⚠️ 规则组不存在", show_alert=True)
            return
            
        # 获取规则组统计信息
        stats = await self.rule_group_service.get_rule_group_stats(rule_group_id)
        
        text = (
            f"📋 规则组: {rule_group.name}\n"
            f"描述: {rule_group.description or '无'}\n\n"
            f"统计信息:\n"
            f"- 群组数: {stats['total_chats']}\n"
            f"- 违规总数: {stats['total_violations']}\n"
            f"- 被禁言用户: {stats['muted_users']}\n"
            f"- 被封禁用户: {stats['banned_users']}\n"
        )
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_rule_group_menu(rule_group_id)
        )
        
    @CallbackRegistry.register(r"^admin:rule_groups:create$")
    async def handle_create_init(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理创建规则组初始化"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        # 存储状态
        context.user_data["creating_rule_group"] = True
        
        keyboard = [[
            InlineKeyboardButton("取消", callback_data="admin:rule_groups:create:cancel")
        ]]
        
        await self._safe_edit_message(
            query,
            "✏️ 创建规则组\n\n"
            "请输入规则组名称：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    @CallbackRegistry.register(r"^admin:rule_groups:create:cancel$")
    async def handle_create_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理取消创建"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        # 清除状态
        context.user_data.pop("creating_rule_group", None)
        context.user_data.pop("rule_group_name", None)
        
        # 返回列表
        await self.handle_rule_groups_list(update, context)
        
    async def handle_create_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组名称输入"""
        if not update.message or not self._is_admin(update.message.from_user.id):
            return
            
        if not context.user_data.get("creating_rule_group"):
            return
            
        # 存储名称
        context.user_data["rule_group_name"] = update.message.text
        
        # 提示输入描述
        keyboard = [[
            InlineKeyboardButton("跳过", callback_data="admin:rule_groups:create:skip_desc"),
            InlineKeyboardButton("取消", callback_data="admin:rule_groups:create:cancel")
        ]]
        
        await update.message.reply_text(
            "✏️ 创建规则组\n\n"
            "请输入规则组描述(可选)：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    @CallbackRegistry.register(r"^admin:rule_groups:create:skip_desc$")
    async def handle_create_skip_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理跳过描述"""
        await self.handle_create_finish(update, context, description=None)
        
    async def handle_create_desc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则组描述输入"""
        if not update.message or not self._is_admin(update.message.from_user.id):
            return
            
        if not context.user_data.get("creating_rule_group"):
            return
            
        await self.handle_create_finish(update, context, description=update.message.text)
        
    async def handle_create_finish(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        description: Optional[str] = None
    ):
        """完成创建规则组"""
        # 创建规则组
        rule_group = await self.rule_group_service.create_rule_group(
            name=context.user_data["rule_group_name"],
            owner_id=update.effective_user.id,
            description=description
        )
        
        # 清除状态
        context.user_data.pop("creating_rule_group", None)
        context.user_data.pop("rule_group_name", None)
        
        if not rule_group:
            await update.effective_message.reply_text(
                "❌ 创建规则组失败",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("返回列表", callback_data="admin:rule_groups:list")
                ]])
            )
            return
            
        # 显示成功消息
        text = (
            "✅ 规则组创建成功\n\n"
            f"名称: {rule_group.name}\n"
            f"描述: {description or '无'}\n"
        )
        
        await update.effective_message.reply_text(
            text,
            reply_markup=self._get_rule_group_menu(rule_group.rule_id)
        )


# 初始化处理器
AdminRuleGroupHandler() 