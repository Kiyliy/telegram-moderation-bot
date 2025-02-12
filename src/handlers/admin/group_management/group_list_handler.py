from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.UserModerationService import UserModerationService
from src.core.database.service.chatsService import ChatService
from datetime import datetime
from typing import List


class AdminGroupListHandler(AdminBaseHandler):
    """群组列表处理器"""
    
    def __init__(self):
        super().__init__()
        self.page_size = 10  # 每页显示条数
        self.moderation_service = UserModerationService()
        self.chat_service = ChatService()

    def _get_pagination_keyboard(
        self, 
        current_page: int,
        has_next: bool,
        base_callback: str,
        back_callback: str = "admin:groups"
    ) -> List[List[InlineKeyboardButton]]:
        """生成分页键盘"""
        keyboard = []
        
        # 分页按钮
        pagination_row = []
        if current_page > 1:
            pagination_row.append(InlineKeyboardButton(
                "« 上一页", 
                callback_data=f"{base_callback}:{current_page-1}"
            ))
        if has_next:
            pagination_row.append(InlineKeyboardButton(
                "下一页 »", 
                callback_data=f"{base_callback}:{current_page+1}"
            ))
        if pagination_row:
            keyboard.append(pagination_row)
            
        # 控制按钮
        keyboard.append([
            InlineKeyboardButton("刷新", callback_data=f"{base_callback}:{current_page}"),
            InlineKeyboardButton("« 返回", callback_data=back_callback)
        ])
        
        return keyboard

    @CallbackRegistry.register(r"^admin:groups:list:(\d+)$")
    async def handle_group_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理群组列表查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        page = int(query.data.split(":")[-1])
        
        # 获取所有群组
        all_groups = await self.chat_service.get_owner_groups(
            user_id=query.from_user.id
        )
        
        # 手动分页
        start_idx = (page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        current_groups = all_groups[start_idx:end_idx]
        has_next = len(all_groups) > end_idx
        
        if not current_groups:
            text = "👥 群组列表\n\n暂无群组"
        else:
            text = "👥 群组列表：\n\n"
            for group in current_groups:
                text += (
                    f"群组: {group.title}\n"
                    f"ID: {group.chat_id}\n"
                    f"类型: {group.chat_type}\n"
                    f"所有者: {group.owner_id}\n"
                    f"------------------------\n"
                )

        keyboard = self._get_pagination_keyboard(
            current_page=page,
            has_next=has_next,
            base_callback="admin:groups:list"
        )
        
        # 如果有记录,添加查看详情按钮
        if current_groups:
            for group in current_groups:
                keyboard.insert(-1, [
                    InlineKeyboardButton(
                        f"查看 {group.title}", 
                        callback_data=f"admin:groups:detail:{group.chat_id}"
                    )
                ])
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:groups:detail:(-?\d+)$")
    async def handle_group_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理群组详情查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        chat_id = int(query.data.split(":")[-1])
        
        # 获取群组信息
        group = await self.chat_service.get_chat_info(chat_id)
        if not group:
            await query.answer("⚠️ 群组不存在", show_alert=True)
            return
            
        # 获取群组违规统计
        violations = await self.moderation_service.get_violation_stats(chat_id=chat_id)
        
        # 获取被封禁用户数量
        banned_users = await self.moderation_service.get_banned_users(chat_id)
        
        text = (
            f"👥 群组详情\n\n"
            f"群组: {group.title}\n"
            f"ID: {group.chat_id}\n"
            f"类型: {group.chat_type}\n"
            f"所有者: {group.owner_id}\n\n"
            f"违规统计:\n"
        )
        
        if violations:
            for vtype, stats in violations.items():
                text += (
                    f"- {vtype}: {stats['count']} 次\n"
                    f"  涉及 {stats['user_count']} 个用户\n"
                )
        else:
            text += "暂无违规记录\n"
            
        text += f"\n被封禁用户: {len(banned_users)} 人"

        keyboard = [
            [
                InlineKeyboardButton("解除绑定", callback_data=f"admin:groups:unbind:{chat_id}"),
                InlineKeyboardButton("查看违规", callback_data=f"admin:groups:violations:{chat_id}:1")
            ],
            [InlineKeyboardButton("« 返回列表", callback_data="admin:groups:list:1")]
        ]
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# 初始化处理器
AdminGroupListHandler() 