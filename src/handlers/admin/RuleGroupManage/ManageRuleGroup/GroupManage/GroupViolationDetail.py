from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.UserModerationService import UserModerationService
from src.core.database.service.chatsService import ChatService
from datetime import datetime


class GroupViolationDetailHandler(AdminBaseHandler):
    """群组违规管理处理器"""
    
    def __init__(self):
        super().__init__()
        self.page_size = 10
        self.moderation_service = UserModerationService()
        self.chat_service = ChatService()
        
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:groups:detail:(-?\d+)$")
    async def handle_group_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理群组详情查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        # 通过回调的字段, 获取群组ID
        rule_group_id = query.data.split(":")[2]
        chat_id = int(query.data.split(":")[-1])
        
        # 获取规则组内的群组信息
        rule_group_chats = await self.chat_service.get_chats_by_rule_group(rule_group_id)
        group = next((g for g in rule_group_chats if g.chat_id == chat_id), None)
        
        if not group:
            await query.answer("⚠️ 该群组不存在或不属于此规则组", show_alert=True)
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
                InlineKeyboardButton("违规统计", callback_data=f"admin:rg:{rule_group_id}:groups:violations:{chat_id}:1"),
                InlineKeyboardButton("封禁用户", callback_data=f"admin:rg:{rule_group_id}:groups:banned:{chat_id}:1")
            ],
            [InlineKeyboardButton("从规则组移除", callback_data=f"admin:rg:{rule_group_id}:groups:unbind:{chat_id}")],
            [InlineKeyboardButton("« 返回列表", callback_data=f"admin:rg:{rule_group_id}:groups:list:1")]
        ]
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:groups:violations:(-?\d+):(\d+)$")
    async def handle_group_violations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理群组违规记录查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        chat_id = int(query.data.split(":")[-2])
        page = int(query.data.split(":")[-1])
        rule_group_id = query.data.split(":")[2]
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
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:groups:detail:{chat_id}")]
        ]
        
        await self._safe_edit_message(
            query,
            text[:4000],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:groups:banned:(-?\d+):(\d+)$")
    async def handle_banned_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理封禁用户管理"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        chat_id = int(query.data.split(":")[-2])
        page = int(query.data.split(":")[-1])
        rule_group_id = query.data.split(":")[2]
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
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:groups:detail:{chat_id}")]
        ]
        
        # 如果有记录,添加解封按钮
        if banned_users:
            for user in banned_users:
                keyboard.insert(-1, [
                    InlineKeyboardButton(
                        f"解封 {user.user_id}", 
                        callback_data=f"admin:rg:{rule_group_id}:groups:unban:{chat_id}:{user.user_id}"
                    )
                ])
        
        await self._safe_edit_message(
            query,
            text[:4000],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:groups:unban:(-?\d+):(\d+)$")
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
GroupViolationDetailHandler() 