from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from .base import AdminBaseHandler
from datetime import datetime, timedelta
import os

class AdminLogHandler(AdminBaseHandler):
    """管理员日志查看处理器"""
    
    def __init__(self):
        super().__init__()
        self.log_dir = "logs"  # 日志目录
        os.makedirs(self.log_dir, exist_ok=True)

    @CallbackRegistry.register(r"^admin:logs$")
    async def handle_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理日志查看回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton("今日日志", callback_data="admin:logs:today"),
             InlineKeyboardButton("本周日志", callback_data="admin:logs:week")],
            [InlineKeyboardButton("违规记录", callback_data="admin:logs:violations"),
             InlineKeyboardButton("操作记录", callback_data="admin:logs:operations")],
            [InlineKeyboardButton("« 返回", callback_data="admin:back")]
        ]

        await self._safe_edit_message(
            query,
            "📋 日志查看\n"
            "请选择要查看的日志类型：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:logs:today$")
    async def handle_today_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理今日日志查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"{today}.log")
        
        if not os.path.exists(log_file):
            text = "📋 今日日志\n\n暂无日志记录"
        else:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()[-20:]  # 只显示最后20行
                text = "📋 今日日志（最新20条）：\n\n" + "".join(logs)

        keyboard = [
            [InlineKeyboardButton("刷新", callback_data="admin:logs:today")],
            [InlineKeyboardButton("« 返回", callback_data="admin:logs")]
        ]
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:logs:week$")
    async def handle_week_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理本周日志查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 获取过去7天的日期
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") 
                for i in range(7)]
        
        keyboard = []
        for date in dates:
            log_file = os.path.join(self.log_dir, f"{date}.log")
            status = "✅" if os.path.exists(log_file) else "❌"
            keyboard.append([InlineKeyboardButton(
                f"{date} {status}",
                callback_data=f"admin:logs:date:{date}"
            )])
            
        keyboard.append([InlineKeyboardButton("« 返回", callback_data="admin:logs")])
        
        await self._safe_edit_message(
            query,
            "📅 本周日志\n"
            "请选择要查看的日期：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:logs:date:(\d{4}-\d{2}-\d{2})$")
    async def handle_date_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理特定日期日志查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        date = query.data.split(":")[-1]
        log_file = os.path.join(self.log_dir, f"{date}.log")
        
        if not os.path.exists(log_file):
            text = f"📋 {date} 日志\n\n暂无日志记录"
        else:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()[-20:]  # 只显示最后20行
                text = f"📋 {date} 日志（最新20条）：\n\n" + "".join(logs)

        keyboard = [
            [InlineKeyboardButton("刷新", callback_data=f"admin:logs:date:{date}")],
            [InlineKeyboardButton("« 返回", callback_data="admin:logs:week")]
        ]
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:logs:violations$")
    async def handle_violations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理违规记录查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        violation_file = os.path.join(self.log_dir, "violations.log")
        
        if not os.path.exists(violation_file):
            text = "📋 违规记录\n\n暂无违规记录"
        else:
            with open(violation_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()[-20:]  # 只显示最后20条
                text = "📋 违规记录（最新20条）：\n\n" + "".join(logs)

        keyboard = [
            [InlineKeyboardButton("刷新", callback_data="admin:logs:violations")],
            [InlineKeyboardButton("« 返回", callback_data="admin:logs")]
        ]
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:logs:operations$")
    async def handle_operations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理操作记录查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        operation_file = os.path.join(self.log_dir, "operations.log")
        
        if not os.path.exists(operation_file):
            text = "📋 操作记录\n\n暂无操作记录"
        else:
            with open(operation_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()[-20:]  # 只显示最后20条
                text = "📋 操作记录（最新20条）：\n\n" + "".join(logs)

        keyboard = [
            [InlineKeyboardButton("刷新", callback_data="admin:logs:operations")],
            [InlineKeyboardButton("« 返回", callback_data="admin:logs")]
        ]
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# 初始化处理器
AdminLogHandler()