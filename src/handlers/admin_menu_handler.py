from src.handlers.base_handler import BaseHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from src.core.config.config import config
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.MessageFilters import MessageFilters
from data.ConfigKeys import ConfigKeys as configkey
from typing import List, Dict, Any
import json
import re

# 具体的处理器类
class AdminMenuHandler(BaseHandler):
    def __init__(self):
        super().__init__()  # 确保调用父类的__init__
        self._load_settings()
        
    def _load_settings(self) -> None:
        """加载管理员设置"""
        self.admin_ids = config.get_config(configkey.bot.ADMIN_IDS, [])
        self.moderation_rules = {
            'nsfw': config.get_config(configkey.bot.settings.moderation.rules.NSFW, True),
            'violence': config.get_config(configkey.bot.settings.moderation.rules.VIOLENCE, True),
            'political': config.get_config(configkey.bot.settings.moderation.rules.POLITICAL, True),
            'spam': config.get_config(configkey.bot.settings.moderation.rules.SPAM, True)
        }
        self.sensitivity = {
            'nsfw': config.get_config(configkey.bot.settings.moderation.sensitivity.NSFW, 0.7),
            'violence': config.get_config(configkey.bot.settings.moderation.sensitivity.VIOLENCE, 0.8),
            'political': config.get_config(configkey.bot.settings.moderation.sensitivity.POLITICAL, 0.6),
            'spam': config.get_config(configkey.bot.settings.moderation.sensitivity.SPAM, 0.5)
        }

    def _is_admin(self, user_id: int) -> bool:
        """检查用户是否是管理员"""
        return user_id in self.admin_ids

    def _get_admin_main_menu(self) -> InlineKeyboardMarkup:
        """获取管理员主菜单键盘"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("审核设置 🛠", callback_data="admin:settings"),
             InlineKeyboardButton("查看日志 📋", callback_data="admin:logs")],
            [InlineKeyboardButton("用户管理 👥", callback_data="admin:users"),
             InlineKeyboardButton("群组管理 👥", callback_data="admin:groups")],
            [InlineKeyboardButton("统计信息 📊", callback_data="admin:stats"),
             InlineKeyboardButton("刷新设置 🔄", callback_data="admin:refresh")]
        ])

    async def _safe_edit_message(self, query, text: str, reply_markup=None) -> None:
        """安全地编辑消息，处理消息未修改的错误"""
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise

    @MessageRegistry.register(MessageFilters.match_prefix(['/admin']))
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /admin 命令"""
        if not update.effective_user or not self._is_admin(update.effective_user.id):
            await update.message.reply_text("⚠️ 抱歉，您没有管理员权限。")
            return

        await update.message.reply_text(
            "👋 欢迎使用管理员控制面板\n"
            "请选择以下功能：",
            reply_markup=self._get_admin_main_menu()
        )

    @CallbackRegistry.register(r"^admin:settings$")
    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理审核设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("审核规则设置", callback_data="admin:settings:rules"),
             InlineKeyboardButton("敏感度设置", callback_data="admin:settings:sensitivity")],
            [InlineKeyboardButton("警告消息设置", callback_data="admin:settings:warning"),
             InlineKeyboardButton("自动处理设置", callback_data="admin:settings:auto")],
            [InlineKeyboardButton("惩罚措施设置", callback_data="admin:settings:punishment")],
            [InlineKeyboardButton("« 返回", callback_data="admin:back")]
        ])

        await self._safe_edit_message(
            query,
            "⚙️ 审核设置\n"
            "请选择要修改的设置项：",
            reply_markup=keyboard
        )

    @CallbackRegistry.register(r"^admin:settings:rules$")
    async def handle_rules_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = []
        for rule, enabled in self.moderation_rules.items():
            status = "✅" if enabled else "❌"
            keyboard.append([InlineKeyboardButton(
                f"{rule.upper()} {status}",
                callback_data=f"admin:settings:rules:toggle:{rule}"
            )])
        
        keyboard.append([InlineKeyboardButton("« 返回设置", callback_data="admin:settings")])
        
        await self._safe_edit_message(
            query,
            "🔧 规则设置\n"
            "点击规则切换开关状态：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:settings:rules:toggle:(\w+)$")
    async def handle_rule_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则开关切换"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 从callback_data中提取规则名称
        rule = query.data.split(":")[-1]
        if rule in self.moderation_rules:
            # 更新内存中的设置
            self.moderation_rules[rule] = not self.moderation_rules[rule]
            
            # 保存到配置文件
            config_key = f"bot.settings.moderation.rules.{rule}"
            config.set_config(config_key, self.moderation_rules[rule])
            
            await query.answer(f"已{'启用' if self.moderation_rules[rule] else '禁用'} {rule.upper()} 规则")
            await self.handle_rules_settings(update, context)

    @CallbackRegistry.register(r"^admin:settings:sensitivity$")
    async def handle_sensitivity_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理敏感度设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 显示当前所有规则的敏感度
        text = "🎚 当前敏感度设置：\n\n"
        keyboard = []
        
        # 显示每个规则的当前敏感度值和调整按钮
        for rule, value in self.sensitivity.items():
            text += f"{rule.upper()}: {value:.2f}\n"
            keyboard.append([InlineKeyboardButton(
                f"调整 {rule.upper()} 敏感度",
                callback_data=f"admin:settings:sensitivity:adjust:{rule}"
            )])

        keyboard.append([InlineKeyboardButton("« 返回设置", callback_data="admin:settings")])
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:settings:sensitivity:adjust:(\w+)$")
    async def handle_sensitivity_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理敏感度调整"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        rule = query.data.split(":")[-1]
        if rule in self.sensitivity:
            # 显示当前值和调整按钮
            current_value = self.sensitivity[rule]
            keyboard = []
            
            # 添加微调按钮
            adjustments = [
                ( 0.05, "➕0.05"),
                (-0.05, "➖0.05"), 
                (-0.1 , "➖0.1" ), 
                ( 0.1 , "➕0.1")
            ]
            
            # 添加调整按钮（每行两个）
            row = []
            for adj_value, label in adjustments:
                new_value = round(current_value + adj_value, 2)
                if 0 <= new_value <= 1:  # 确保值在有效范围内
                    row.append(InlineKeyboardButton(
                        label,
                        callback_data=f"admin:settings:sensitivity:set:{rule}:{new_value}"
                    ))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:  # 如果还有剩余的按钮
                keyboard.append(row)
            
            # 添加直接设置的按钮
            presets = [(0.3, "低"), (0.5, "中"), (0.7, "高"), (0.9, "严格")]
            row = []
            for value, label in presets:
                row.append(InlineKeyboardButton(
                    label,
                    callback_data=f"admin:settings:sensitivity:set:{rule}:{value}"
                ))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("« 返回", callback_data="admin:settings:sensitivity")])
            
            await self._safe_edit_message(
                query,
                f"🎚 调整 {rule.upper()} 敏感度\n"
                f"当前值: {current_value:.2f}\n\n"
                f"• 使用 ➕/➖ 按钮微调\n"
                f"• 或选择预设等级\n"
                f"（0 最宽松，1 最严格）",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    @CallbackRegistry.register(r"^admin:settings:sensitivity:set:(\w+):(\d*\.?\d*)$")
    async def handle_sensitivity_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理敏感度设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 从callback_data中提取规则名称和新值
        rule = query.data.split(":")[-2]
        new_value = float(query.data.split(":")[-1])
        
        if rule in self.sensitivity and 0 <= new_value <= 1:
            # 更新内存中的设置
            self.sensitivity[rule] = new_value
            
            # 保存到配置文件
            config_key = f"bot.settings.moderation.sensitivity.{rule}"
            config.set_config(config_key, new_value)
            
            await query.answer(f"已将 {rule.upper()} 敏感度设置为 {new_value:.2f}")
            # 返回到调整界面，显示新的值
            await self.handle_sensitivity_adjust(update, context)

    @CallbackRegistry.register(r"^admin:refresh$")
    async def handle_refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理刷新设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        self._load_settings()
        await query.answer("✅ 设置已刷新")
        # 避免重复编辑相同的消息
        if query.message:
            await self._safe_edit_message(
                query,
                "👋 欢迎使用管理员控制面板\n"
                "请选择以下功能：",
                reply_markup=self._get_admin_main_menu()
            )

    @CallbackRegistry.register(r"^admin:logs$")
    async def handle_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理日志查看回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("今日日志", callback_data="admin:logs:today"),
             InlineKeyboardButton("本周日志", callback_data="admin:logs:week")],
            [InlineKeyboardButton("违规记录", callback_data="admin:logs:violations"),
             InlineKeyboardButton("操作记录", callback_data="admin:logs:operations")],
            [InlineKeyboardButton("« 返回", callback_data="admin:back")]
        ])

        await query.edit_message_text(
            "📋 日志查看\n"
            "请选择要查看的日志类型：",
            reply_markup=keyboard
        )

    @CallbackRegistry.register(r"^admin:users$")
    async def handle_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理用户管理回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("查看封禁用户", callback_data="admin:users:banned"),
             InlineKeyboardButton("查看禁言用户", callback_data="admin:users:muted")],
            [InlineKeyboardButton("用户搜索", callback_data="admin:users:search"),
             InlineKeyboardButton("批量操作", callback_data="admin:users:batch")],
            [InlineKeyboardButton("« 返回", callback_data="admin:back")]
        ])

        await query.edit_message_text(
            "👥 用户管理\n"
            "请选择管理操作：",
            reply_markup=keyboard
        )

    @CallbackRegistry.register(r"^admin:back$")
    async def handle_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理返回主菜单回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        await self._safe_edit_message(
            query,
            "👋 欢迎使用管理员控制面板\n"
            "请选择以下功能：",
            reply_markup=self._get_admin_main_menu()
        )


# 在应用启动时初始化
AdminMenuHandler()