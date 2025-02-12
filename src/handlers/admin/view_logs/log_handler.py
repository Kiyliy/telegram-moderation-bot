from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from datetime import datetime, timedelta
from typing import List, Tuple
import os

class AdminLogHandler(AdminBaseHandler):
    """管理员日志查看处理器"""
    
    def __init__(self):
        super().__init__()
        self.log_dir = "logs"  # 日志目录
        self.page_size = 10  # 每页显示条数
        os.makedirs(self.log_dir, exist_ok=True)

    def _read_log_file(self, file_path: str, page: int = 1) -> Tuple[List[str], int]:
        """
        读取日志文件，支持分页
        
        Args:
            file_path: 日志文件路径
            page: 页码（从1开始）
            
        Returns:
            (日志列表, 总页数)
        """
        if not os.path.exists(file_path):
            return [], 0
            
        with open(file_path, 'r', encoding='utf-8') as f:
            all_logs = f.readlines()
            
        # 计算总页数
        total_pages = (len(all_logs) + self.page_size - 1) // self.page_size
        
        # 确保页码有效
        page = min(max(1, page), total_pages) if total_pages > 0 else 1
        
        # 计算当前页的日志
        start_idx = (total_pages - page) * self.page_size  # 倒序显示，最新的在第1页
        end_idx = start_idx + self.page_size
        page_logs = all_logs[start_idx:end_idx]
        
        return page_logs, total_pages

    def _get_pagination_keyboard(self, current_page: int, total_pages: int, base_callback: str) -> List[List[InlineKeyboardButton]]:
        """生成分页键盘"""
        keyboard = []
        
        # 分页按钮
        pagination_row = []
        if current_page < total_pages:  # 因为是倒序，所以这里判断相反
            pagination_row.append(InlineKeyboardButton(
                "« 上一页", 
                callback_data=f"{base_callback}:{current_page+1}"
            ))
        if current_page > 1:
            pagination_row.append(InlineKeyboardButton(
                "下一页 »", 
                callback_data=f"{base_callback}:{current_page-1}"
            ))
        if pagination_row:
            keyboard.append(pagination_row)
            
        # 页码信息
        if total_pages > 1:
            keyboard.append([InlineKeyboardButton(
                f"第 {current_page}/{total_pages} 页",
                callback_data="noop"  # 这个按钮不会触发任何操作
            )])
        
        # 控制按钮
        keyboard.append([
            InlineKeyboardButton("刷新", callback_data=f"{base_callback}:{current_page}"),
            InlineKeyboardButton("« 返回", callback_data="admin:logs")
        ])
        
        return keyboard

    @CallbackRegistry.register(r"^admin:logs$")
    async def handle_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理日志查看回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        keyboard = [
            [InlineKeyboardButton("今日日志", callback_data="admin:logs:today:1"),
             InlineKeyboardButton("本周日志", callback_data="admin:logs:week")],
            [InlineKeyboardButton("违规记录", callback_data="admin:logs:violations:1"),
             InlineKeyboardButton("操作记录", callback_data="admin:logs:operations:1")],
            [InlineKeyboardButton("« 返回", callback_data="admin:back")]
        ]

        await self._safe_edit_message(
            query,
            "📋 日志查看\n"
            "请选择要查看的日志类型：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:logs:today:(\d+)$")
    async def handle_today_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理今日日志查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        page = int(query.data.split(":")[-1])
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"{today}.log")
        
        logs, total_pages = self._read_log_file(log_file, page)
        
        if not logs:
            text = "📋 今日日志\n\n暂无日志记录"
        else:
            text = f"📋 今日日志：\n\n" + "".join(logs)
        
        keyboard = self._get_pagination_keyboard(page, total_pages, "admin:logs:today")
        
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
                callback_data=f"admin:logs:date:{date}:1"
            )])
            
        keyboard.append([InlineKeyboardButton("« 返回", callback_data="admin:logs")])
        
        await self._safe_edit_message(
            query,
            "📅 本周日志\n"
            "请选择要查看的日期：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:logs:date:(\d{4}-\d{2}-\d{2}):(\d+)$")
    async def handle_date_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理特定日期日志查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        date = query.data.split(":")[-2]
        page = int(query.data.split(":")[-1])
        log_file = os.path.join(self.log_dir, f"{date}.log")
        
        logs, total_pages = self._read_log_file(log_file, page)
        
        if not logs:
            text = f"📋 {date} 日志\n\n暂无日志记录"
        else:
            text = f"📋 {date} 日志：\n\n" + "".join(logs)

        keyboard = self._get_pagination_keyboard(page, total_pages, f"admin:logs:date:{date}")
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:logs:violations:(\d+)$")
    async def handle_violations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理违规记录查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        page = int(query.data.split(":")[-1])
        violation_file = os.path.join(self.log_dir, "violations.log")
        
        logs, total_pages = self._read_log_file(violation_file, page)
        
        if not logs:
            text = "📋 违规记录\n\n暂无违规记录"
        else:
            text = "📋 违规记录：\n\n" + "".join(logs)

        keyboard = self._get_pagination_keyboard(page, total_pages, "admin:logs:violations")
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:logs:operations:(\d+)$")
    async def handle_operations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理操作记录查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        page = int(query.data.split(":")[-1])
        operation_file = os.path.join(self.log_dir, "operations.log")
        
        logs, total_pages = self._read_log_file(operation_file, page)
        
        if not logs:
            text = "📋 操作记录\n\n暂无操作记录"
        else:
            text = "📋 操作记录：\n\n" + "".join(logs)

        keyboard = self._get_pagination_keyboard(page, total_pages, "admin:logs:operations")
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# 初始化处理器
AdminLogHandler()