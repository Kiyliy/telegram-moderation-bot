from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.UserModerationService import UserModerationService
from src.core.database.service.chatsService import ChatService
from datetime import datetime
from typing import List
from src.core.database.models.db_chat import ChatInfo

class GroupListHandler(AdminBaseHandler):
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
        back_callback: str = r"admin:rg:{rule_group_id}:groups",
        bot_username: str = "",
        rule_group_id: str = ""
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
            InlineKeyboardButton("🔗 添加新的群组", url=f"https://t.me/{bot_username}?startgroup=true"),
            InlineKeyboardButton("🔗 绑定已有的群组", callback_data=f"admin:rg:{rule_group_id}:groups:bind_existing")
        ])
        keyboard.append([
            InlineKeyboardButton("🔄 刷新", callback_data=f"{base_callback}:{current_page}"),
            InlineKeyboardButton("🔙 返回", callback_data=back_callback.format(rule_group_id=rule_group_id))
        ])

        
        return keyboard

    @CallbackRegistry.register(r"^admin:rg:.{16}:groups:list:(\d+)$")
    async def handle_group_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理群组列表查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        page = int(query.data.split(":")[-1]) if len(query.data.split(":")) > 5 else 1
        rule_group_id = query.data.split(":")[2]    
        
        # 获取所有群组
        all_groups:List[ChatInfo] = await self.chat_service.get_chats_by_rule_group(
            rule_group_id=rule_group_id
        )
        
        # 手动分页
        start_idx = (page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        current_groups = all_groups[start_idx:end_idx]
        has_next = len(all_groups) > end_idx
        
        if not current_groups:
            text = "👥 此规则组下的群组列表\n\n暂无群组"
        else:
            text = "👥 此规则组下的群组列表：\n\n"
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
            base_callback=f"admin:rg:{rule_group_id}:groups:list",
            bot_username=context.bot.username,
            rule_group_id=rule_group_id
        )
        
        # 如果有记录,添加查看详情按钮
        if current_groups:
            for group in current_groups:
                keyboard.insert(0, [
                    InlineKeyboardButton(
                        f"{group.title}", 
                        callback_data=f"admin:rg:{rule_group_id}:groups:detail:{group.chat_id}"
                    )
                ])
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )




# 初始化处理器
GroupListHandler() 