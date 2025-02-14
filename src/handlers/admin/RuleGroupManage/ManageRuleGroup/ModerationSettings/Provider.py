from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
from typing import Optional
from src.core.registry.CallbackRegistry import CallbackRegistry


# src/handlers/admin/RuleGroupManage/ViewRuleGroup/RuleGroupEdit/ModerationSettings/ProviderSelectHandler.py
class ProviderSelectHandler(AdminBaseHandler):
    def __init__(self):
        super().__init__()
    
    def _get_provider_keyboard(self, rule_group_id: str, current_provider: str, provider_list: list) -> InlineKeyboardMarkup:
        """获取Provider选择键盘"""
        keyboard = []
        for provider in provider_list:  # 从配置文件中获取的provider列表
            keyboard.append([
                InlineKeyboardButton(
                    f"{provider} {'✓' if provider == current_provider else ''}",
                    callback_data=f"admin:rg:{rule_group_id}:mo:provider:set:{provider}"
                )
            ])
        keyboard.append([
            InlineKeyboardButton(
                "« 返回",
                callback_data=f"admin:rg:{rule_group_id}:mo:menu"
            )
        ])
        return InlineKeyboardMarkup(keyboard)
    
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:provider:list$")
    async def provider_list_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """选择供应商列表"""
        query = update.callback_query
        rule_group_id = query.data.split(":")[2]
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
        
        # 获取当前provider
        current_provider = await rule_group_config.get_config(
            rule_group_id,
            configkey.moderation.ACTIVE_PROVIDER
        ) or "openai"  # 默认使用openai
        
        # 获取可用的provider列表
        provider_list = await rule_group_config.get_config(
            rule_group_id,
            configkey.moderation.PROVIDER_LIST
        ) or ["openai"]  # 默认只有openai
        
        text = "🔧 Provider 设置\n\n"
        text += f"当前使用: {current_provider}\n\n"
        text += "选择要使用的 Provider:"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_provider_keyboard(rule_group_id, current_provider, provider_list)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:provider:set:(\w+)$")
    async def handle_provider_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理Provider设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
        
        rule_group_id = query.data.split(":")[2]
        new_provider = query.data.split(":")[-1]
        
        try:
            # 更新当前provider
            await rule_group_config.set_config(
                rule_group_id,
                configkey.moderation.ACTIVE_PROVIDER,
                new_provider
            )
            
            await query.answer(f"✅ 已切换到 {new_provider}")
            
            # 刷新provider列表界面
            await self.provider_list_handler(update, context)
            
        except Exception as e:
            print(f"[ERROR] 设置Provider失败: {e}")
            await query.answer("⚠️ 发生错误，请重试", show_alert=True)

ProviderSelectHandler()