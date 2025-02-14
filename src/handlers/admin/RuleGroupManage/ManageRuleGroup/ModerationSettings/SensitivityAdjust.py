from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey


class SensitivityAdjustHandler(AdminBaseHandler):
    """敏感度设置处理器"""

    def __init__(self):
        super().__init__()

    def _get_sensitivity_keyboard(self, rule_group_id: str, provider_sensitivities: dict) -> InlineKeyboardMarkup:
        """获取敏感度设置键盘"""
        keyboard = []
        row = []
        
        # 从配置中动态生成按钮
        for rule_name, value in provider_sensitivities.items():
            button = InlineKeyboardButton(
                f"{rule_name}",
                callback_data=f"admin:rg:{rule_group_id}:mo:sen:adjust:{rule_name.lower()}"
            )
            row.append(button)
            
            # 每两个按钮一行
            if len(row) == 2:
                keyboard.append(row)
                row = []
                
        # 如果还有剩余的单个按钮
        if row:
            keyboard.append(row)
            
        keyboard.append([InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:mo:menu")])
        return InlineKeyboardMarkup(keyboard)

    def _get_adjust_keyboard(self, rule_group_id: str, rule_type: str, current_value: float) -> InlineKeyboardMarkup:
        """获取调整敏感度键盘"""
        keyboard = []

        # 添加微调按钮
        adjustments = [
            (-0.1, "➖0.1"), (-0.05, "➖0.05"),
            (0.05, "➕0.05"), (0.1, "➕0.1")
        ]
        row = []
        for adj_value, label in adjustments:
            new_value = round(current_value + adj_value, 2)
            if 0 <= new_value <= 1:
                row.append(InlineKeyboardButton(
                    label,
                    callback_data=f"admin:rg:{rule_group_id}:mo:sen:set:{rule_type}:{new_value}"
                ))
            if len(row) == 2:
                keyboard.append(row)
                row = []

        # 添加预设值按钮
        presets = [(0.3, "低"), (0.5, "中"), (0.7, "高"), (0.9, "严格")]
        row = []
        for value, label in presets:
            row.append(InlineKeyboardButton(
                label,
                callback_data=f"admin:rg:{rule_group_id}:mo:sen:set:{rule_type}:{value}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        keyboard.append([InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:mo:sen:menu")])
        return InlineKeyboardMarkup(keyboard)

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:sen(:menu)?$")
    async def handle_sensitivity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理敏感度设置"""
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
        
        # 获取这个provider的敏感度json
        provider_sensitivities = await rule_group_config.get_config(
            rule_group_id,
            getattr(getattr(configkey.moderation.providers, current_provider.lower()), "SENSITIVITY")
        )
        
        # 将配置key标准化处理
        provider_sensitivities_fix = {}
        for key, value in provider_sensitivities.items():
            provider_sensitivities_fix[key.upper().replace("/", "_").replace("-", "_")] = value

        text = f"⚙️ 敏感度设置 (Provider: {current_provider})\n\n"
        text += "当前状态:\n"
        for rule_name, value in provider_sensitivities_fix.items():
            text += f"- {rule_name}: {value}\n"

        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_sensitivity_keyboard(rule_group_id, provider_sensitivities_fix)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:sen:adjust:(\w+)$")
    async def handle_sensitivity_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理敏感度调整"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        rule_group_id = query.data.split(":")[2]
        rule_type = query.data.split(":")[6]

        # 重构：根据当前 provider 获取对应的敏感度配置键
        current_provider = await rule_group_config.get_config(
            rule_group_id,
            configkey.moderation.ACTIVE_PROVIDER
        ) or "openai"

        # 获取当前的rule的数值
        current = await rule_group_config.get_config(
            rule_group_id,
            getattr(getattr(getattr(configkey.moderation.providers, current_provider.lower()), "sensitivity"), rule_type.upper())
        )
        
        # 如果配置值为字符串（例如 "low"/"medium"/"high"），则转换为数值
        if isinstance(current, str):
            value_map = {"low": 0.3, "medium": 0.5, "high": 0.7}
            current = value_map.get(current.lower(), 0.5)
        else:
            current = float(current or 0.5)

        text = f"🎚 调整 {rule_type.upper()} 敏感度\n"
        text += f"当前值: {current:.2f}\n\n"
        text += "• 使用 ➕/➖ 按钮微调\n"
        text += "• 或选择预设等级\n"
        text += "（0 最宽松，1 最严格）"

        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_adjust_keyboard(rule_group_id, rule_type, current)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:sen:set:(\w+):(\d*\.?\d*)$")
    async def handle_sensitivity_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理敏感度设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        rule_group_id = query.data.split(":")[2]
        rule_type = query.data.split(":")[-2]
        try:
            new_value = float(query.data.split(":")[-1])
            if not (0 <= new_value <= 1):
                await query.answer("⚠️ 无效的值", show_alert=True)
                return

            # 获取当前 provider
            current_provider = await rule_group_config.get_config(
                rule_group_id,
                configkey.moderation.ACTIVE_PROVIDER
            ) or "openai"
            
            # 设置新的数值
            await rule_group_config.set_config(
                rule_group_id,
                getattr(getattr(getattr(configkey.moderation.providers, current_provider.lower()), "sensitivity"), rule_type.upper()),
                new_value
            )

            await query.answer(f"✅ 已设置 {rule_type.upper()} 敏感度为 {new_value:.2f}")

            # 刷新调整界面
            await self.handle_sensitivity_adjust(update, context)

        except Exception as e:
            print(f"[ERROR] 设置敏感度失败: {e}")
            await query.answer("⚠️ 发生错误，请重试", show_alert=True)


# 初始化处理器
SensitivityAdjustHandler()