from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.config.config import config
from data.ConfigKeys import ConfigKeys as configkey
from .base import AdminBaseHandler
from src.core.registry.MessageFilters import MessageFilters
from src.core.registry.MessageRegistry import MessageRegistry
import re

class AdminWarningHandler(AdminBaseHandler):
    """管理员警告消息设置处理器"""
    
    def __init__(self):
        super().__init__()
        self._load_warning_settings()
        
    def _load_warning_settings(self) -> None:
        """加载警告消息设置"""
        self.warning_messages = {
            'nsfw': config.get_config(configkey.bot.settings.warning_messages.NSFW, 
                "⚠️ 您发送的内容包含不适当的内容，已被自动删除。"),
            'violence': config.get_config(configkey.bot.settings.warning_messages.VIOLENCE,
                "⚠️ 您发送的内容包含暴力内容，已被自动删除。"),
            'political': config.get_config(configkey.bot.settings.warning_messages.POLITICAL,
                "⚠️ 您发送的内容包含敏感内容，已被自动删除。"),
            'spam': config.get_config(configkey.bot.settings.warning_messages.SPAM,
                "⚠️ 您发送的内容被判定为垃圾信息，已被自动删除。")
        }

    @CallbackRegistry.register(r"^admin:settings:warning$")
    async def handle_warning_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理警告消息设置回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = []
        for rule, message in self.warning_messages.items():
            keyboard.append([InlineKeyboardButton(
                f"修改 {rule.upper()} 警告消息",
                callback_data=f"admin:settings:warning:edit:{rule}"
            )])
        
        keyboard.append([InlineKeyboardButton("« 返回设置", callback_data="admin:settings")])
        
        text = "📝 警告消息设置\n\n"
        for rule, message in self.warning_messages.items():
            text += f"{rule.upper()}:\n{message}\n\n"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        
    @MessageRegistry.register(MessageFilters.match_reply_msg_regex(r"✏️ 编辑 (\w+) 警告消息"))
    async def handle_warning_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理警告消息编辑"""
        if not self._is_admin(update.effective_user.id):
            return
            
        # 从正则匹配中提取规则名
        match = re.search(r"✏️ 编辑 (\w+) 警告消息", update.message.reply_to_message.text)
        if not match:
            return
            
        rule = match.group(1).lower()  # 转小写
        if rule not in self.warning_messages:
            return
            
        # 更新警告消息
        new_message = update.message.text
        self.warning_messages[rule] = new_message
        config_key = f"bot.settings.warning_messages.{rule}"
        config.set_config(config_key, new_message)
        
        # 发送确认消息
        await update.message.reply_text(
            f"✅ {rule.upper()} 警告消息已更新为:\n{new_message}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("返回警告消息设置", callback_data="admin:settings:warning")
            ]])
        )

    @CallbackRegistry.register(r"^admin:settings:warning:edit:(\w+)$")
    async def handle_warning_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理编辑警告消息"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        rule = query.data.split(":")[-1]
        if rule not in self.warning_messages:
            await query.answer("⚠️ 无效的规则", show_alert=True)
            return
            
        # 存储当前正在编辑的规则
        context.user_data['editing_warning'] = rule
        
        await self._safe_edit_message(
            query,
            f"✏️ 编辑 {rule.upper()} 警告消息\n"
            f"当前消息:\n{self.warning_messages[rule]}\n\n"
            "请直接引用此消息发送新的警告消息，或点击取消返回。",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("取消", callback_data="admin:settings:warning")
            ]])
        )



# 初始化处理器
AdminWarningHandler() 