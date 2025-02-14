from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey


class PunishmentHandler(AdminBaseHandler):
    """惩罚设置处理器"""
    
    def __init__(self):
        super().__init__()
        
    def _get_setting_map(self):
        setting_map = {
            "mute": configkey.punishment.MUTE_DURATIONS,
            "ban": configkey.punishment.BAN_THRESHOLD,
            "reset": configkey.punishment.WARNING_RESET_DAYS,
            "max": configkey.punishment.MAX_WARNINGS
        }
        return setting_map
        
    def _get_punishment_keyboard(self, rule_group_id: str) -> InlineKeyboardMarkup:
        """获取惩罚设置键盘"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "禁言时长",
                    callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute"
                ),
                InlineKeyboardButton(
                    "封禁阈值",
                    callback_data=f"admin:rg:{rule_group_id}:mo:punishment:ban"
                )
            ],
            [
                InlineKeyboardButton(
                    "警告重置天数",
                    callback_data=f"admin:rg:{rule_group_id}:mo:punishment:reset"
                ),
                InlineKeyboardButton(
                    "最大警告次数",
                    callback_data=f"admin:rg:{rule_group_id}:mo:punishment:max"
                )
            ],
            [InlineKeyboardButton("« 返回设置", callback_data=f"admin:rg:{rule_group_id}:mo")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:punishment$")
    async def handle_punishment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理惩罚设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        
        # 获取当前惩罚设置
        punishment = {
            "mute_duration": await rule_group_config.get_config(
                rule_group_id,
                configkey.punishment.MUTE_DURATIONS
            ),
            "ban_threshold": await rule_group_config.get_config(
                rule_group_id,
                configkey.punishment.BAN_THRESHOLD
            ),
            "warning_reset_days": await rule_group_config.get_config(
                rule_group_id,
                configkey.punishment.WARNING_RESET_DAYS
            ),
            "max_warnings": await rule_group_config.get_config(
                rule_group_id,
                configkey.punishment.MAX_WARNINGS
            )
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
        
    def _get_value_adjust_keyboard(self, rule_group_id: str, setting_keyword: str, current_value: int | list) -> InlineKeyboardMarkup:
        """获取数值调整键盘"""
        if setting_keyword == "mute":
            # 为禁言时长创建特殊键盘
            keyboard = []
            mute_durations = current_value if isinstance(current_value, list) else []
            
            # 添加现有的禁言时长显示
            for i, duration in enumerate(mute_durations):
                row = [
                    InlineKeyboardButton(f"#{i+1}: {duration}分钟", callback_data="ignore"),
                    InlineKeyboardButton("删除", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:del:{i}")
                ]
                keyboard.append(row)
            
            # 添加新增按钮
            keyboard.append([
                InlineKeyboardButton("➕ 添加新禁言时长", 
                    callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:add")
            ])
            keyboard.append([
                InlineKeyboardButton("« 返回", 
                    callback_data=f"admin:rg:{rule_group_id}:mo:punishment")
            ])
            return InlineKeyboardMarkup(keyboard)
            
        # 其他设置保持原样
        step_map = {
            "ban": 1,       # 封禁阈值步长1次
            "reset": 1,     # 重置天数步长1天
            "max": 1        # 最大警告步长1次
        }
        step = step_map[setting_keyword]
        
        keyboard = [
            [
                InlineKeyboardButton(f"-{step*2}", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:{setting_keyword}:adj:-{step*2}"),
                InlineKeyboardButton(f"-{step}", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:{setting_keyword}:adj:-{step}"),
                InlineKeyboardButton(f"{current_value}", callback_data="ignore"),
                InlineKeyboardButton(f"+{step}", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:{setting_keyword}:adj:{step}"),
                InlineKeyboardButton(f"+{step*2}", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:{setting_keyword}:adj:{step*2}")
            ],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:mo:punishment")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:punishment:(mute|ban|reset|max)$")
    async def handle_punishment_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理惩罚设置编辑"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        parts = query.data.split(":")
        rule_group_id = parts[2]
        setting_type = parts[-1]
        
        # 获取当前设置
        setting_map = self._get_setting_map()
        
        current = await rule_group_config.get_config(
            rule_group_id,
            setting_map[setting_type]
        )
        
        # 获取设置说明
        setting_desc = {
            "mute": "禁言时长(分钟)",
            "ban": "封禁阈值(次数)",
            "reset": "警告重置天数",
            "max": "最大警告次数"
        }
        
        text = f"⚙️ {setting_desc[setting_type]}设置\n\n"
        text += f"当前值: {current}\n\n"
        text += "点击按钮调整数值:"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_value_adjust_keyboard(rule_group_id, setting_type, current)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:punishment:(mute|ban|reset|max):adj:(-?\d+)$")
    async def handle_punishment_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理惩罚设置调整"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        # 获取配置键和当前值
        setting_map = self._get_setting_map()
        
        parts = query.data.split(":")
        rule_group_id = parts[2]
        setting_keyword = parts[5] 
        adjustment = int(parts[-1])
        
        setting_type = setting_map[setting_keyword]

        current = await rule_group_config.get_config(
            rule_group_id,
            key=setting_type
        )
        
        # 计算新值（确保不小于1）
        new_value = max(1, current + adjustment)
        
        # 更新设置
        await rule_group_config.set_config(
            rule_group_id,
            setting_type,
            new_value
        )
        
        # 获取设置说明
        setting_desc = {
            "mute": "禁言时长(分钟)",
            "ban": "封禁阈值(次数)",
            "reset": "警告重置天数",
            "max": "最大警告次数"
        }
        
        text = f"⚙️ {setting_desc[setting_keyword]}设置\n\n"
        text += f"当前值: {new_value}\n\n"
        text += "点击按钮调整数值:"
        
        await query.answer(f"已更新为: {new_value}")
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_value_adjust_keyboard(rule_group_id, setting_type, new_value)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:punishment:mute:(add|del:\d+)$")
    async def handle_mute_duration_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理禁言时长的添加和删除"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        parts = query.data.split(":")
        rule_group_id = parts[2]
        action = parts[6]
        del_index = parts[7] if len(parts) > 7 else None
        
        current_durations = await rule_group_config.get_config(
            rule_group_id,
            configkey.punishment.MUTE_DURATIONS
        )
        
        if action == "add":
            # 显示时间单位选择键盘
            keyboard = [
                [
                    InlineKeyboardButton("30分钟", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:set:30"),
                    InlineKeyboardButton("1小时", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:set:60"),
                    InlineKeyboardButton("2小时", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:set:120")
                ],
                [
                    InlineKeyboardButton("6小时", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:set:360"),
                    InlineKeyboardButton("12小时", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:set:720"),
                    InlineKeyboardButton("1天", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:set:1440")
                ],
                [
                    InlineKeyboardButton("3天", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:set:4320"),
                    InlineKeyboardButton("1周", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:set:10080"),
                    InlineKeyboardButton("永久", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute:set:-1")
                ],
                [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:mo:punishment:mute")]
            ]
            text = "选择要添加的禁言时长："
            await self._safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        elif action.startswith("del"):
            index = int(del_index)
            if 0 <= index < len(current_durations):
                current_durations.pop(index)
                await rule_group_config.set_config(
                    rule_group_id,
                    configkey.punishment.MUTE_DURATIONS,
                    current_durations
                )
                await query.answer("已删除该禁言时长")
        
        # 刷新禁言时长设置界面
        text = "⚙️ 禁言时长设置\n\n"
        text += "当前设置的禁言时长序列:\n"
        for i, duration in enumerate(current_durations):
            text += f"第{i+1}次: {duration}分钟\n"
        text += "\n点击按钮进行调整:"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_value_adjust_keyboard(rule_group_id, "mute", current_durations)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:punishment:mute:set:(-?\d+)$")
    async def handle_mute_duration_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理设置新的禁言时长"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        parts = query.data.split(":")
        rule_group_id = parts[2]
        duration = int(parts[-1])
        
        current_durations = await rule_group_config.get_config(
            rule_group_id,
            configkey.punishment.MUTE_DURATIONS
        )
        
        current_durations.append(duration)
        # current_durations.sort()  # 按时间长短排序
        
        await rule_group_config.set_config(
            rule_group_id,
            configkey.punishment.MUTE_DURATIONS,
            current_durations
        )
        
        await query.answer("已添加新的禁言时长")
        
        # 返回禁言时长设置界面
        text = "⚙️ 禁言时长设置\n\n"
        text += "当前设置的禁言时长序列:\n"
        for i, duration in enumerate(current_durations):
            text += f"第{i+1}次: {duration}分钟\n"
        text += "\n点击按钮进行调整:"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_value_adjust_keyboard(rule_group_id, "mute", current_durations)
        )


# 初始化处理器
PunishmentHandler() 