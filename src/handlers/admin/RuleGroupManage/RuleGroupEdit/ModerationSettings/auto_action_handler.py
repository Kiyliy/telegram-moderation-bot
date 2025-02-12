from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.config.config import config
from data.ConfigKeys import ConfigKeys as configkey
from src.handlers.admin.base import AdminBaseHandler

class AdminAutoActionHandler(AdminBaseHandler):
    """管理员自动处理设置处理器"""
    
    def __init__(self):
        super().__init__()
        self._load_auto_action_settings()
        
    def _load_auto_action_settings(self) -> None:
        """加载自动处理设置"""
        self.auto_actions = {
            'delete_message': config.get_config(configkey.bot.settings.moderation.auto_actions.DELETE_MESSAGE, True),
            'warn_user': config.get_config(configkey.bot.settings.moderation.auto_actions.WARN_USER, True),
            'notify_admins': config.get_config(configkey.bot.settings.moderation.auto_actions.NOTIFY_ADMINS, True)
        }

    @CallbackRegistry.register(r"^admin:settings:auto$")
    async def handle_auto_action_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理自动处理设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = []
        action_names = {
            'delete_message': '删除消息',
            'warn_user': '警告用户',
            'notify_admins': '通知管理员'
        }
        
        for action, enabled in self.auto_actions.items():
            status = "✅" if enabled else "❌"
            keyboard.append([InlineKeyboardButton(
                f"{action_names[action]} {status}",
                callback_data=f"admin:settings:auto:toggle:{action}"
            )])
        
        keyboard.append([InlineKeyboardButton("« 返回设置", callback_data="admin:settings")])
        
        await self._safe_edit_message(
            query,
            "⚙️ 自动处理设置\n"
            "点击选项切换开关状态：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:settings:auto:toggle:(\w+)$")
    async def handle_auto_action_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理自动处理开关切换"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        action = query.data.split(":")[-1]
        if action in self.auto_actions:
            # 更新内存中的设置
            self.auto_actions[action] = not self.auto_actions[action]
            
            # 保存到配置文件
            config_key = f"bot.settings.moderation.auto_actions.{action}"
            config.set_config(config_key, self.auto_actions[action])
            
            action_names = {
                'delete_message': '删除消息',
                'warn_user': '警告用户',
                'notify_admins': '通知管理员'
            }
            
            await query.answer(
                f"已{'启用' if self.auto_actions[action] else '禁用'} {action_names[action]}"
            )
            await self.handle_auto_action_settings(update, context)

# 初始化处理器
AdminAutoActionHandler() 