from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey

class EnableSettingHandler(AdminBaseHandler):
    """管理员审核设置处理器"""
    
    def __init__(self):
        super().__init__()
        
    def _get_rules_keyboard(self, rule_group_id: str, nsfw: bool, spam: bool, violence: bool, political: bool) -> InlineKeyboardMarkup:
        """获取规则设置键盘"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "NSFW √" if nsfw else "NSFW 检测 ❌",
                    callback_data=f"admin:rg:{rule_group_id}:mo:rules:toggle:nsfw"
                ),
                InlineKeyboardButton(
                    "垃圾信息 √" if spam else "垃圾信息 ❌",
                    callback_data=f"admin:rg:{rule_group_id}:mo:rules:toggle:spam"
                )
            ],
            [
                InlineKeyboardButton(
                    "暴力内容 √" if violence else "暴力内容 ❌",
                    callback_data=f"admin:rg:{rule_group_id}:mo:rules:toggle:violence"
                ),
                InlineKeyboardButton(
                    "政治内容 √" if political else "政治内容 ❌",
                    callback_data=f"admin:rg:{rule_group_id}:mo:rules:toggle:political"
                )
            ],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:mo:menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:rules$")
    async def handle_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        
        # 获取当前规则状态
        rules = {
            "nsfw": await rule_group_config.get_config(rule_group_id, configkey.moderation.rules.NSFW),
            "spam": await rule_group_config.get_config(rule_group_id, configkey.moderation.rules.SPAM),
            "violence": await rule_group_config.get_config(rule_group_id, configkey.moderation.rules.VIOLENCE),
            "political": await rule_group_config.get_config(rule_group_id, configkey.moderation.rules.POLITICAL)
        }
        
        text = "⚙️ 审核规则设置\n\n"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_rules_keyboard(rule_group_id, rules['nsfw'], rules['spam'], rules['violence'], rules['political'])
        )
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:rules:toggle:(\w+)$")
    async def handle_rule_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则开关切换"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        rule_type = query.data.split(":")[-1]
        
        # 获取当前状态
        current = await rule_group_config.get_config(
            rule_group_id,
            getattr(configkey.moderation.rules, rule_type.upper())
        )
        
        # 切换状态
        await rule_group_config.set_config(
            rule_group_id,
            getattr(configkey.moderation.rules, rule_type.upper()),
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