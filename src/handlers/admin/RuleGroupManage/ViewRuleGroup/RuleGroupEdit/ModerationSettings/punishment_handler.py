from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey


class AdminPunishmentHandler(AdminBaseHandler):
    """惩罚设置处理器"""
    
    def __init__(self):
        super().__init__()
        # 移除_load_punishment_settings,因为现在是从rule_group_config获取
        
    def _get_punishment_keyboard(self, rule_group_id: str) -> InlineKeyboardMarkup:
        """获取惩罚设置键盘"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "禁言时长",
                    callback_data=f"admin:settings:punishment:mute:{rule_group_id}"
                ),
                InlineKeyboardButton(
                    "封禁阈值",
                    callback_data=f"admin:settings:punishment:ban:{rule_group_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "警告重置天数",
                    callback_data=f"admin:settings:punishment:reset:{rule_group_id}"
                ),
                InlineKeyboardButton(
                    "最大警告次数",
                    callback_data=f"admin:settings:punishment:max:{rule_group_id}"
                )
            ],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rule_groups:select:{rule_group_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:settings:punishment:(\w+)$")
    async def handle_punishment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理惩罚设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[-1]
        
        # 获取当前惩罚设置
        punishment = {
            "mute_duration": await rule_group_config.get_config(rule_group_id, configkey.Punishment.MUTE_DURATION),
            "ban_threshold": await rule_group_config.get_config(rule_group_id, configkey.Punishment.BAN_THRESHOLD),
            "warning_reset_days": await rule_group_config.get_config(rule_group_id, configkey.Punishment.WARNING_RESET_DAYS),
            "max_warnings": await rule_group_config.get_config(rule_group_id, configkey.Punishment.MAX_WARNINGS)
        }
        
        text = "⚙️ 惩罚设置\n\n"
        text += "当前设置:\n"
        text += f"- 禁言时长: {punishment['mute_duration']} 分钟\n"
        text += f"- 封禁阈值: {punishment['ban_threshold']} 次\n"
        text += f"- 警告重置天数: {punishment['warning_reset_days']} 天\n"
        text += f"- 最大警告次数: {punishment['max_warnings']} 次\n"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_punishment_keyboard(rule_group_id)
        )
        
    @CallbackRegistry.register(r"^admin:settings:punishment:(mute|ban|reset|max):(\w+)$")
    async def handle_punishment_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理惩罚设置编辑"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        setting_type = query.data.split(":")[-2]
        rule_group_id = query.data.split(":")[-1]
        
        # 获取当前设置
        setting_map = {
            "mute": configkey.Punishment.MUTE_DURATION,
            "ban": configkey.Punishment.BAN_THRESHOLD,
            "reset": configkey.Punishment.WARNING_RESET_DAYS,
            "max": configkey.Punishment.MAX_WARNINGS
        }
        
        current = await rule_group_config.get_config(
            rule_group_id,
            setting_map[setting_type]
        )
        
        # 保存编辑状态
        context.user_data["punishment_edit"] = {
            "rule_group_id": rule_group_id,
            "setting_type": setting_type
        }
        
        # 获取设置说明
        setting_desc = {
            "mute": "禁言时长(分钟)",
            "ban": "封禁阈值(次数)",
            "reset": "警告重置天数",
            "max": "最大警告次数"
        }
        
        text = f"⚙️ {setting_desc[setting_type]}设置\n\n"
        text += f"当前值: {current}\n\n"
        text += "请发送新的数值:"
        
        keyboard = [[InlineKeyboardButton(
            "« 返回",
            callback_data=f"admin:settings:punishment:{rule_group_id}"
        )]]
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    async def handle_punishment_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理惩罚设置值输入"""
        if not self._is_admin(update.message.from_user.id):
            await update.message.reply_text("⚠️ 没有权限")
            return
            
        # 检查是否在编辑状态
        if "punishment_edit" not in context.user_data:
            return
            
        edit_state = context.user_data["punishment_edit"]
        rule_group_id = edit_state["rule_group_id"]
        setting_type = edit_state["setting_type"]
        
        # 检查输入是否为数字
        try:
            value = int(update.message.text)
            if value <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ 请输入大于0的数字")
            return
            
        # 获取配置键
        setting_map = {
            "mute": configkey.Punishment.MUTE_DURATION,
            "ban": configkey.Punishment.BAN_THRESHOLD,
            "reset": configkey.Punishment.WARNING_RESET_DAYS,
            "max": configkey.Punishment.MAX_WARNINGS
        }
        
        # 更新设置
        await rule_group_config.set_config(
            rule_group_id,
            setting_map[setting_type],
            value
        )
        
        # 清除编辑状态
        del context.user_data["punishment_edit"]
        
        # 发送确认消息
        setting_desc = {
            "mute": "禁言时长",
            "ban": "封禁阈值",
            "reset": "警告重置天数",
            "max": "最大警告次数"
        }
        
        text = f"✅ 已更新{setting_desc[setting_type]}: {value}"
        keyboard = [[InlineKeyboardButton(
            "返回设置",
            callback_data=f"admin:settings:punishment:{rule_group_id}"
        )]]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# 初始化处理器
AdminPunishmentHandler() 