from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.config.config import config
from data.ConfigKeys import ConfigKeys as configkey
from src.handlers.admin.base import AdminBaseHandler
from src.core.registry.MessageFilters import MessageFilters
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey
import re

class WarningHandler(AdminBaseHandler):
    """警告消息设置处理器"""
    
    def __init__(self):
        super().__init__()
        
    def _get_warning_keyboard(self, rule_group_id: str) -> InlineKeyboardMarkup:
        """获取警告消息设置键盘"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "NSFW 警告",
                    callback_data=f"admin:rg:{rule_group_id}:mo:warning:nsfw"
                ),
                InlineKeyboardButton(
                    "垃圾信息",
                    callback_data=f"admin:rg:{rule_group_id}:mo:warning:spam"
                )
            ],
            [
                InlineKeyboardButton(
                    "暴力内容",
                    callback_data=f"admin:rg:{rule_group_id}:mo:warning:violence"
                ),
                InlineKeyboardButton(
                    "政治内容",
                    callback_data=f"admin:rg:{rule_group_id}:mo:warning:political"
                )
            ],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:mo")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:warning$")
    async def handle_warning(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看当前规则组的警告消息设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        
        # 获取当前警告消息
        warnings = {
            "nsfw": await rule_group_config.get_config(rule_group_id, configkey.warning_messages.NSFW),
            "spam": await rule_group_config.get_config(rule_group_id, configkey.warning_messages.SPAM),
            "violence": await rule_group_config.get_config(rule_group_id, configkey.warning_messages.VIOLENCE),
            "political": await rule_group_config.get_config(rule_group_id, configkey.warning_messages.POLITICAL)
        }
        
        text = "⚙️ 警告消息设置\n\n"
        text += "当前消息:\n"
        text += f"- NSFW 警告: {warnings['nsfw']}\n"
        text += f"- 垃圾信息: {warnings['spam']}\n"
        text += f"- 暴力内容: {warnings['violence']}\n"
        text += f"- 政治内容: {warnings['political']}\n"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_warning_keyboard(rule_group_id)
        )
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:mo:warning:(\w+)$")
    async def handle_warning_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """进入警告消息的编辑状态"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        rule_type = query.data.split(":")[-1]
        
        # 获取当前警告消息
        current = await rule_group_config.get_config(
            rule_group_id,
            getattr(configkey.warning_messages, rule_type.upper())
        )
        
        text = f"⚙️ {rule_type.upper()} 警告消息设置\n\n"
        text += f"rule_group_id: {rule_group_id}\n"
        text += f"当前消息:\n{current}\n\n"
        text += "✏️ 请输入新的警告消息:\n"
        text += "（回复此消息输入新的警告消息）"
        
        keyboard = [[InlineKeyboardButton(
            "« 返回",
            callback_data=f"admin:rg:{rule_group_id}:mo:warning"
        )]]
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    @MessageRegistry.register(MessageFilters.match_reply_msg_regex(r".*请输入新的警告消息.*"))
    async def handle_warning_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理警告消息输入"""
        if not self._is_admin(update.message.from_user.id):
            await update.message.reply_text("⚠️ 没有权限")
            return
            
        # 从回复的消息中提取rule_type
        reply_msg = update.message.reply_to_message.text
        rule_type = re.search(r"⚙️ (\w+) 警告消息设置", reply_msg).group(1).lower()
        rule_group_id = re.search(r"rule_group_id: (\w+)", reply_msg).group(1)
        
        # 更新警告消息
        await rule_group_config.set_config(
            rule_group_id,
            getattr(configkey.warning_messages, rule_type.upper()),
            update.message.text
        )
        
        # 发送确认消息
        text = f"✅ 已更新 {rule_type} 警告消息"
        keyboard = [[InlineKeyboardButton(
            "返回设置",
            callback_data=f"admin:rg:{rule_group_id}:mo:warning"
        )]]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# 初始化处理器
WarningHandler() 