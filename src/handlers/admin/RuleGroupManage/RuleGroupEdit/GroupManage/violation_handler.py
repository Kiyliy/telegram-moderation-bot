from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.UserModerationService import UserModerationService
from datetime import datetime


class AdminGroupViolationHandler(AdminBaseHandler):
    """群组违规管理处理器"""
    
    def __init__(self):
        super().__init__()
        self.page_size = 10
        self.moderation_service = UserModerationService()

    @CallbackRegistry.register(r"^admin:groups:violations:(-?\d+):(\d+)$")
    async def handle_group_violations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理群组违规记录查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        chat_id = int(query.data.split(":")[-2])
        page = int(query.data.split(":")[-1])
        offset = (page - 1) * self.page_size
        
        # 获取群组违规记录
        violations = await self.moderation_service.get_chat_violations(
            chat_id=chat_id,
            limit=self.page_size
        )
        
        if not violations:
            text = "📋 违规记录\n\n暂无违规记录"
        else:
            text = "📋 违规记录：\n\n"
            for v in violations:
                text += (
                    f"用户: {v.user_id}\n"
                    f"类型: {v.violation_type}\n"
                    f"操作: {v.action}\n"
                    f"时间: {datetime.fromtimestamp(v.created_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"------------------------\n"
                )

        keyboard = [
            [InlineKeyboardButton("« 返回", callback_data=f"admin:groups:detail:{chat_id}")]
        ]
        
        await self._safe_edit_message(
            query,
            text[:4000],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:groups:banned:(-?\d+):(\d+)$")
    async def handle_banned_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理封禁用户管理"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        chat_id = int(query.data.split(":")[-2])
        page = int(query.data.split(":")[-1])
        
        # 获取被封禁用户
        banned_users = await self.moderation_service.get_banned_users(chat_id)
        
        if not banned_users:
            text = "👥 封禁用户\n\n暂无被封禁用户"
        else:
            text = "👥 封禁用户：\n\n"
            for user in banned_users:
                text += (
                    f"用户ID: {user.user_id}\n"
                    f"警告次数: {user.warning_count}\n"
                    f"封禁时间: {datetime.fromtimestamp(user.banned_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"------------------------\n"
                )

        keyboard = [
            [InlineKeyboardButton("« 返回", callback_data=f"admin:groups:detail:{chat_id}")]
        ]
        
        # 如果有记录,添加解封按钮
        if banned_users:
            for user in banned_users:
                keyboard.insert(-1, [
                    InlineKeyboardButton(
                        f"解封 {user.user_id}", 
                        callback_data=f"admin:groups:unban:{chat_id}:{user.user_id}"
                    )
                ])
        
        await self._safe_edit_message(
            query,
            text[:4000],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:groups:unban:(-?\d+):(\d+)$")
    async def handle_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理解除封禁"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        chat_id = int(query.data.split(":")[-2])
        user_id = int(query.data.split(":")[-1])
        
        # 解除封禁
        result = await self.moderation_service.unban_user(user_id, chat_id)
        
        if result:
            await query.answer("✅ 解封成功", show_alert=True)
        else:
            await query.answer("❌ 解封失败", show_alert=True)
            
        # 刷新页面
        await self.handle_banned_users(update, context)


# 初始化处理器
AdminGroupViolationHandler() 