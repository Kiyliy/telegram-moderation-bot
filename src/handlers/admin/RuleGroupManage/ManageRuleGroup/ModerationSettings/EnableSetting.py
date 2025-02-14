from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
from src.core.moderation.types.CategoryTypes import CategorySettings

class EnableSettingHandler(AdminBaseHandler):
    """管理员审核设置处理器"""
    
    def __init__(self):
        super().__init__()
        
    def _get_rules_keyboard(
            self, 
            rule_group_id: str, 
            provider_categories: CategorySettings
        ) -> InlineKeyboardMarkup:
        """
        获取规则设置键盘
        provider_obj_list的作用是, 作为callback_data
        """
        keyboard = []
        row = []
        
        # 从配置中获取的rules动态生成按钮
        for rule_name, enabled in provider_categories.items():
            button = InlineKeyboardButton(
                f"{rule_name} {'✅' if enabled else '❌'}", 
                callback_data=f"admin:rg:{rule_group_id}:mo:rules:toggle:{rule_name.lower()}"
            )
            row.append(button)
            
            # 每两个按钮一行
            if len(row) == 1:
                keyboard.append(row)
                row = []
                
        # 如果还有剩余的单个按钮
        if row:
            keyboard.append(row)
            
        # 添加返回按钮
        keyboard.append([InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:mo:menu")])
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:rules$")
    async def handle_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则设置"""
        query = update.callback_query
        
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        
        # 获取当前provider
        current_provider = await rule_group_config.get_config(
            rule_group_id,
            configkey.moderation.ACTIVE_PROVIDER
        ) or "openai"
        
        # 获取这个provider的配置文件
        provider_categories = await rule_group_config.get_config(
            rule_group_id,
            getattr(getattr(configkey.moderation.providers, current_provider.lower()), 'CATEGORIES')
        )
            
        # 将/替换为_ 以作为回调的callback_data
        provider_categories_fix = {}
        for key, value in provider_categories.items():
            provider_categories_fix[key.upper().replace("/", "_")] = value
        
        text = f"⚙️ 审核规则设置 (Provider: {current_provider})\n\n"
        text += "请选择要启用的规则检测项:"
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_rules_keyboard(rule_group_id, provider_categories_fix)
        )
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:rules:toggle:.*$")
    async def handle_rule_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则开关切换"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        rule_type = query.data.split(":")[-1] 
        
        # 获取当前provider
        current_provider = await rule_group_config.get_config(
            rule_group_id,
            configkey.moderation.ACTIVE_PROVIDER
        ) or "openai"
        
        # 获取当前状态
        current = await rule_group_config.get_config(
            rule_group_id,
            getattr(getattr(getattr(configkey.moderation.providers, current_provider.lower()), 'categories'), rule_type.upper())
        )
        
        # 切换状态
        await rule_group_config.set_config(
            rule_group_id,
            getattr(getattr(getattr(configkey.moderation.providers, current_provider.lower()), 'categories'), rule_type.upper()),
            not current
        )
        
        await query.answer(
            f"{'✅ 已启用' if not current else '❌ 已禁用'} {rule_type} 检测",
            show_alert=True
        )
        
        # 刷新界面
        await self.handle_rules(update, context)

# 初始化处理器
EnableSettingHandler() 