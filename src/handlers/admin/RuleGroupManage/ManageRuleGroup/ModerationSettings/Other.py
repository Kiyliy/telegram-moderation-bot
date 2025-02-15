from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey

class OtherHandler(AdminBaseHandler):
    """其它设置处理器"""
    
    def __init__(self):
        super().__init__()
        
    def _get_other_keyboard(self, rule_group_id: str, skip_manager: bool) -> InlineKeyboardMarkup:
        """获取其它设置键盘"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "跳过管理员 ✅" if skip_manager else "跳过管理员 ❌",
                    callback_data=f"admin:rg:{rule_group_id}:mo:other:skip_manager"
                )
            ],
            [InlineKeyboardButton("« 返回设置", callback_data=f"admin:rg:{rule_group_id}:mo")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:other$")
    async def handle_other(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理其它设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        
        # 获取当前其它设置
        other_config = {
            "skip_manager": await rule_group_config.get_config(
                rule_group_id,
                configkey.moderation.other_config.SKIP_MANAGER
            )
        }
        
        text = "⚙️ 其它设置\n\n"
        text += f"跳过管理员: {'✅' if other_config['skip_manager'] else '❌'}\n"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_other_keyboard(rule_group_id, other_config['skip_manager'])
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:other:skip_manager$")
    async def handle_skip_manager_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理跳过管理员开关切换"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        
        # 获取当前设置
        current = await rule_group_config.get_config(
            rule_group_id,
            configkey.moderation.other_config.SKIP_MANAGER
        )
        
        # 切换设置
        new_value = not current
        
        # 更新设置
        await rule_group_config.set_config(
            rule_group_id,
            configkey.moderation.other_config.SKIP_MANAGER,
            new_value
        )
        
        # 刷新其它设置界面
        text = "⚙️ 其它设置\n\n"
        
        await query.answer(f"已更新为: {'✅' if new_value else '❌'}")
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_other_keyboard(rule_group_id, new_value)
        )

# 初始化处理器
OtherHandler() 

