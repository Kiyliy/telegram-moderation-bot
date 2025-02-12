from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
from src.handlers.admin.base import AdminBaseHandler

class AutoActionHandler(AdminBaseHandler):
    """管理员自动处理设置处理器"""
    
    def __init__(self):
        super().__init__()

    async def _load_auto_action_settings(self, rule_group_id: str) -> None:
        """加载自动处理设置"""
        self.auto_actions = {
            'delete_message': await rule_group_config.get_config(
                rule_group_id,
                configkey.moderation.auto_actions.DELETE_MESSAGE,
                True
            ),
            'warn_user': await rule_group_config.get_config(
                rule_group_id,
                configkey.moderation.auto_actions.WARN_USER,
                True
            ),
            'notify_admins': await rule_group_config.get_config(
                rule_group_id,
                configkey.moderation.auto_actions.NOTIFY_ADMINS,
                True
            )
        }

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:auto$")
    async def handle_auto_action_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理自动处理设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        rule_group_id = query.data.split(":")[2]  # 获取规则组ID
        await self._load_auto_action_settings(rule_group_id)  # 加载当前规则组的设置
        
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
                callback_data=f"admin:rg:{rule_group_id}:mo:auto:toggle:{action}"
            )])
        
        keyboard.append([InlineKeyboardButton("« 返回设置", callback_data=f"admin:rg:{rule_group_id}:mo")])
        
        await self._safe_edit_message(
            query,
            "⚙️ 自动处理设置\n"
            "点击选项切换开关状态：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:auto:toggle:(\w+)$")
    async def handle_auto_action_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理自动处理开关切换"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        parts = query.data.split(":")
        rule_group_id = parts[2]  # 获取规则组ID
        action = parts[-1]  # 获取动作类型
        
        await self._load_auto_action_settings(rule_group_id)  # 加载当前规则组的设置

        if action in self.auto_actions:
            # 更新内存中的设置
            self.auto_actions[action] = not self.auto_actions[action]
            
            # 保存到配置文件
            config_mapping = {
                'delete_message': configkey.moderation.auto_actions.DELETE_MESSAGE,
                'warn_user': configkey.moderation.auto_actions.WARN_USER,
                'notify_admins': configkey.moderation.auto_actions.NOTIFY_ADMINS
            }
            
            await rule_group_config.set_config(
                rule_group_id,
                config_mapping[action],
                self.auto_actions[action]
            )
            
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
AutoActionHandler() 