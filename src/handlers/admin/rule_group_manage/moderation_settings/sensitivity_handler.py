from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey


class AdminSensitivityHandler(AdminBaseHandler):
    """敏感度设置处理器"""
    
    def __init__(self):
        super().__init__()
        
    def _get_sensitivity_keyboard(self, rule_group_id: str) -> InlineKeyboardMarkup:
        """获取敏感度设置键盘"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "NSFW 敏感度",
                    callback_data=f"admin:settings:sensitivity:adjust:{rule_group_id}:nsfw"
                ),
                InlineKeyboardButton(
                    "垃圾信息",
                    callback_data=f"admin:settings:sensitivity:adjust:{rule_group_id}:spam"
                )
            ],
            [
                InlineKeyboardButton(
                    "暴力内容",
                    callback_data=f"admin:settings:sensitivity:adjust:{rule_group_id}:violence"
                ),
                InlineKeyboardButton(
                    "政治内容",
                    callback_data=f"admin:settings:sensitivity:adjust:{rule_group_id}:political"
                )
            ],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rule_groups:select:{rule_group_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    def _get_adjust_keyboard(self, rule_group_id: str, rule_type: str) -> InlineKeyboardMarkup:
        """获取调整敏感度键盘"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "低",
                    callback_data=f"admin:settings:sensitivity:set:{rule_group_id}:{rule_type}:low"
                ),
                InlineKeyboardButton(
                    "中",
                    callback_data=f"admin:settings:sensitivity:set:{rule_group_id}:{rule_type}:medium"
                ),
                InlineKeyboardButton(
                    "高",
                    callback_data=f"admin:settings:sensitivity:set:{rule_group_id}:{rule_type}:high"
                )
            ],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:settings:sensitivity:{rule_group_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:settings:sensitivity:(\w+)$")
    async def handle_sensitivity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理敏感度设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[-1]
        
        # 获取当前敏感度
        sensitivity = {
            "nsfw": await rule_group_config.get_config(rule_group_id, configkey.Sensitivity.NSFW),
            "spam": await rule_group_config.get_config(rule_group_id, configkey.Sensitivity.SPAM),
            "violence": await rule_group_config.get_config(rule_group_id, configkey.Sensitivity.VIOLENCE),
            "political": await rule_group_config.get_config(rule_group_id, configkey.Sensitivity.POLITICAL)
        }
        
        text = "⚙️ 敏感度设置\n\n"
        text += "当前状态:\n"
        text += f"- NSFW 检测: {sensitivity['nsfw']}\n"
        text += f"- 垃圾信息: {sensitivity['spam']}\n"
        text += f"- 暴力内容: {sensitivity['violence']}\n"
        text += f"- 政治内容: {sensitivity['political']}\n"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_sensitivity_keyboard(rule_group_id)
        )
        
    @CallbackRegistry.register(r"^admin:settings:sensitivity:adjust:(\w+):(\w+)$")
    async def handle_sensitivity_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理敏感度调整"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[-2]
        rule_type = query.data.split(":")[-1]
        
        # 获取当前敏感度
        current = await rule_group_config.get_config(
            rule_group_id,
            getattr(configkey.Sensitivity, rule_type.upper())
        )
        
        text = f"⚙️ {rule_type.upper()} 敏感度设置\n\n"
        text += f"当前敏感度: {current}\n\n"
        text += "选择新的敏感度级别:"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_adjust_keyboard(rule_group_id, rule_type)
        )
        
    @CallbackRegistry.register(r"^admin:settings:sensitivity:set:(\w+):(\w+):(\w+)$")
    async def handle_sensitivity_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理敏感度设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[-3]
        rule_type = query.data.split(":")[-2]
        level = query.data.split(":")[-1]
        
        # 更新敏感度
        await rule_group_config.set_config(
            rule_group_id,
            getattr(configkey.Sensitivity, rule_type.upper()),
            level
        )
        
        await query.answer(f"✅ 已设置 {rule_type} 敏感度为 {level}", show_alert=True)
        
        # 刷新界面
        await self.handle_sensitivity(update, context)


# 初始化处理器
AdminSensitivityHandler() 