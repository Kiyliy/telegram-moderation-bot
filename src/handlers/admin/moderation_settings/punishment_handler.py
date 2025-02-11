from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.config.config import config
from data.ConfigKeys import ConfigKeys as configkey
from ..base import AdminBaseHandler
from typing import List

class AdminPunishmentHandler(AdminBaseHandler):
    """管理员惩罚措施设置处理器"""
    
    def __init__(self):
        super().__init__()
        self._load_punishment_settings()
        
    def _load_punishment_settings(self) -> None:
        """加载惩罚措施设置"""
        self.mute_durations = config.get_config(configkey.bot.settings.punishment.MUTE_DURATIONS, [300, 3600, 86400])
        self.ban_threshold = config.get_config(configkey.bot.settings.punishment.BAN_THRESHOLD, 5)

    @CallbackRegistry.register(r"^admin:settings:punishment$")
    async def handle_punishment_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理惩罚措施设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton("禁言时长设置", callback_data="admin:settings:punishment:mute")],
            [InlineKeyboardButton("封禁阈值设置", callback_data="admin:settings:punishment:ban")],
            [InlineKeyboardButton("« 返回设置", callback_data="admin:settings")]
        ]
        
        text = "⚖️ 惩罚措施设置\n\n"
        text += "当前禁言时长：\n"
        for duration in self.mute_durations:
            text += f"• {self._format_duration(duration)}\n"
        text += f"\n封禁阈值：{self.ban_threshold} 次警告"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{seconds // 60}分钟"
        elif seconds < 86400:
            return f"{seconds // 3600}小时"
        else:
            return f"{seconds // 86400}天"

    @CallbackRegistry.register(r"^admin:settings:punishment:mute$")
    async def handle_mute_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理禁言时长设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = []
        # 添加预设时长选项
        presets = [
            (300, "5分钟"), 
            (900, "15分钟"),
            (3600, "1小时"), 
            (7200, "2小时"),
            (86400, "1天"),
            (259200, "3天")
        ]
        
        row = []
        for duration, label in presets:
            row.append(InlineKeyboardButton(
                f"添加 {label}",
                callback_data=f"admin:settings:punishment:mute:add:{duration}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
            
        # 添加当前时长的删除按钮
        for duration in self.mute_durations:
            keyboard.append([InlineKeyboardButton(
                f"删除 {self._format_duration(duration)}",
                callback_data=f"admin:settings:punishment:mute:del:{duration}"
            )])
            
        keyboard.append([InlineKeyboardButton("« 返回", callback_data="admin:settings:punishment")])
        
        await self._safe_edit_message(
            query,
            "⏱ 禁言时长设置\n"
            "当前时长列表：\n" +
            "\n".join([f"• {self._format_duration(d)}" for d in self.mute_durations]) +
            "\n\n选择要添加或删除的时长：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:settings:punishment:mute:(add|del):(\d+)$")
    async def handle_mute_duration_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理禁言时长添加/删除"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        action = query.data.split(":")[-2]
        duration = int(query.data.split(":")[-1])
        
        if action == "add" and duration not in self.mute_durations:
            self.mute_durations.append(duration)
            self.mute_durations.sort()  # 保持时长有序
        elif action == "del" and duration in self.mute_durations:
            self.mute_durations.remove(duration)
            
        # 保存到配置文件
        config.set_config(configkey.bot.settings.punishment.MUTE_DURATIONS, self.mute_durations)
        
        await query.answer(
            f"已{'添加' if action == 'add' else '删除'}禁言时长: {self._format_duration(duration)}"
        )
        await self.handle_mute_settings(update, context)

    @CallbackRegistry.register(r"^admin:settings:punishment:ban$")
    async def handle_ban_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理封禁阈值设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = []
        # 添加阈值调整按钮
        adjustments = [(-1, "➖1"), (1, "➕1"), (-5, "➖5"), (5, "➕5")]
        row = []
        for adj_value, label in adjustments:
            new_value = self.ban_threshold + adj_value
            if new_value > 0:  # 确保阈值大于0
                row.append(InlineKeyboardButton(
                    label,
                    callback_data=f"admin:settings:punishment:ban:set:{new_value}"
                ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
            
        # 添加预设值
        presets = [(3, "低"), (5, "中"), (10, "高")]
        row = []
        for value, label in presets:
            row.append(InlineKeyboardButton(
                label,
                callback_data=f"admin:settings:punishment:ban:set:{value}"
            ))
        keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("« 返回", callback_data="admin:settings:punishment")])
        
        await self._safe_edit_message(
            query,
            f"🚫 封禁阈值设置\n"
            f"当前阈值: {self.ban_threshold} 次警告\n\n"
            f"• 使用 ➕/➖ 按钮调整\n"
            f"• 或选择预设等级",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:settings:punishment:ban:set:(\d+)$")
    async def handle_ban_threshold_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理封禁阈值设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        new_value = int(query.data.split(":")[-1])
        if new_value <= 0:
            await query.answer("⚠️ 阈值必须大于0", show_alert=True)
            return
            
        # 更新阈值
        self.ban_threshold = new_value
        config.set_config(configkey.bot.settings.punishment.BAN_THRESHOLD, new_value)
        
        await query.answer(f"已将封禁阈值设置为: {new_value}")
        await self.handle_ban_settings(update, context)

# 初始化处理器
AdminPunishmentHandler() 