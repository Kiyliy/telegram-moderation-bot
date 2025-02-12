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

class AdminWarningHandler(AdminBaseHandler):
    """警告消息设置处理器"""
    
    def __init__(self):
        super().__init__()
        
    def _get_warning_keyboard(self, rule_group_id: str) -> InlineKeyboardMarkup:
        """获取警告消息设置键盘"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "NSFW 警告",
                    callback_data=f"admin:settings:warning:{rule_group_id}:nsfw"
                ),
                InlineKeyboardButton(
                    "垃圾信息",
                    callback_data=f"admin:settings:warning:{rule_group_id}:spam"
                )
            ],
            [
                InlineKeyboardButton(
                    "暴力内容",
                    callback_data=f"admin:settings:warning:{rule_group_id}:violence"
                ),
                InlineKeyboardButton(
                    "政治内容",
                    callback_data=f"admin:settings:warning:{rule_group_id}:political"
                )
            ],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rule_groups:select:{rule_group_id}")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:settings:warning:(\w+)$")
    async def handle_warning(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理警告消息设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[-1]
        
        # 获取当前警告消息
        warnings = {
            "nsfw": await rule_group_config.get_config(rule_group_id, configkey.WarningMessages.NSFW),
            "spam": await rule_group_config.get_config(rule_group_id, configkey.WarningMessages.SPAM),
            "violence": await rule_group_config.get_config(rule_group_id, configkey.WarningMessages.VIOLENCE),
            "political": await rule_group_config.get_config(rule_group_id, configkey.WarningMessages.POLITICAL)
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
        
    @CallbackRegistry.register(r"^admin:settings:warning:(\w+):(\w+)$")
    async def handle_warning_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理警告消息编辑"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[-2]
        rule_type = query.data.split(":")[-1]
        
        # 获取当前警告消息
        current = await rule_group_config.get_config(
            rule_group_id,
            getattr(configkey.WarningMessages, rule_type.upper())
        )
        
        # 保存编辑状态
        context.user_data["warning_edit"] = {
            "rule_group_id": rule_group_id,
            "rule_type": rule_type
        }
        
        text = f"⚙️ {rule_type.upper()} 警告消息设置\n\n"
        text += f"当前消息:\n{current}\n\n"
        text += "请发送新的警告消息:"
        
        keyboard = [[InlineKeyboardButton(
            "« 返回",
            callback_data=f"admin:settings:warning:{rule_group_id}"
        )]]
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    async def handle_warning_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理警告消息输入"""
        if not self._is_admin(update.message.from_user.id):
            await update.message.reply_text("⚠️ 没有权限")
            return
            
        # 检查是否在编辑状态
        if "warning_edit" not in context.user_data:
            return
            
        edit_state = context.user_data["warning_edit"]
        rule_group_id = edit_state["rule_group_id"]
        rule_type = edit_state["rule_type"]
        
        # 更新警告消息
        await rule_group_config.set_config(
            rule_group_id,
            getattr(configkey.WarningMessages, rule_type.upper()),
            update.message.text
        )
        
        # 清除编辑状态
        del context.user_data["warning_edit"]
        
        # 发送确认消息
        text = f"✅ 已更新 {rule_type} 警告消息"
        keyboard = [[InlineKeyboardButton(
            "返回设置",
            callback_data=f"admin:settings:warning:{rule_group_id}"
        )]]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# 初始化处理器
AdminWarningHandler() 