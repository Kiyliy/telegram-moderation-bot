from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.ModerationLogService import ModerationLogService
from src.core.database.service.UserModerationService import UserModerationService
from src.core.database.service.chatsService import ChatService
from datetime import datetime
import time
from typing import List


class AdminLogHandler(AdminBaseHandler):
    """管理员日志查看处理器"""
    
    def __init__(self):
        super().__init__()
        self.page_size = 10  # 每页显示条数
        self.moderation_log_service = ModerationLogService()
        self.user_moderation_service = UserModerationService()
        self.chat_service = ChatService()

    def _get_pagination_keyboard(
        self, 
        current_page: int,
        has_next: bool,
        base_callback: str,
        rule_group_id: str,
        back_callback: str = None
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
            InlineKeyboardButton("« 返回", callback_data=back_callback or f"admin:rg:{rule_group_id}")
        ])
        
        return keyboard

    @CallbackRegistry.register(r"^admin:rg:.{16}:logs$")
    async def handle_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理日志查看回调"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        rule_group_id = query.data.split(":")[2]

        # 获取规则组下的所有群组
        chats = await self.chat_service.get_chats_by_rule_group(rule_group_id)
        chat_ids = [chat.chat_id for chat in chats]

        # 获取待审核申诉数量
        pending_appeals = await self.moderation_log_service.get_pending_appeals(
            limit=1,
            chat_ids=chat_ids
        )
        pending_count = len(pending_appeals)

        keyboard = [
            [InlineKeyboardButton(
                f"待处理申诉 ({pending_count})", 
                callback_data=f"admin:rg:{rule_group_id}:logs:pending:1"
            )],
            [InlineKeyboardButton("违规记录", callback_data=f"admin:rg:{rule_group_id}:logs:violations:1"),
             InlineKeyboardButton("审核记录", callback_data=f"admin:rg:{rule_group_id}:logs:reviews:1")],
            [InlineKeyboardButton("审核统计", callback_data=f"admin:rg:{rule_group_id}:logs:stats"),
             InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}")]
        ]

        await self._safe_edit_message(
            query,
            "📋 审核日志查看\n"
            "请选择要查看的内容：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:logs:pending:(\d+)$")
    async def handle_pending_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理待审核日志查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        rule_group_id = query.data.split(":")[2]
        page = int(query.data.split(":")[-1])
        offset = (page - 1) * self.page_size
        
        # 获取规则组下的所有群组
        chats = await self.chat_service.get_chats_by_rule_group(rule_group_id)
        chat_ids = [chat.chat_id for chat in chats]
        
        # 获取待审核申诉
        logs = await self.moderation_log_service.get_pending_appeals(
            limit=self.page_size + 1,  # 多获取一条用于判断是否有下一页
            offset=offset,
            chat_ids=chat_ids
        )
        
        has_next = len(logs) > self.page_size
        logs = logs[:self.page_size]  # 去掉多获取的一条
        
        if not logs:
            text = "📋 待处理申诉\n\n暂无待处理的申诉"
        else:
            text = "📋 待处理申诉：\n\n"
            for log in logs:
                text += (
                    f"ID: {log.id}\n"
                    f"用户: {log.user_id}\n"
                    f"群组: {log.chat_id}\n"
                    f"类型: {log.violation_type or '未知'}\n"
                    f"内容: {log.content[:100] + '...' if len(log.content or '') > 100 else log.content}\n"
                    f"置信度: {log.confidence or 'N/A'}\n"
                    f"申诉理由: {log.appeal_reason}\n"
                    f"申诉时间: {datetime.fromtimestamp(log.appeal_time).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"------------------------\n"
                )

        keyboard = self._get_pagination_keyboard(
            current_page=page,
            has_next=has_next,
            base_callback=f"admin:rg:{rule_group_id}:logs:pending",
            rule_group_id=rule_group_id,
            back_callback=f"admin:rg:{rule_group_id}:logs"
        )
        
        # 如果有记录,添加审核按钮
        if logs:
            for log in logs:
                keyboard.insert(-1, [
                    InlineKeyboardButton(
                        f"✅ 通过 #{log.id}", 
                        callback_data=f"admin:rg:{rule_group_id}:logs:approve:{log.id}"
                    ),
                    InlineKeyboardButton(
                        f"❌ 驳回 #{log.id}",
                        callback_data=f"admin:rg:{rule_group_id}:logs:reject:{log.id}"
                    )
                ])
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:logs:(approve|reject):(\d+)$")
    async def handle_review_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理审核操作"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        action = query.data.split(":")[4]
        log_id = int(query.data.split(":")[-1])
        
        # 更新审核状态
        success = await self.moderation_log_service.update_review_status(
            log_id=log_id,
            review_status="approved" if action == "approve" else "rejected",
            reviewer_id=query.from_user.id
        )
        
        if success:
            await query.answer(
                f"✅ 已{'通过' if action == 'approve' else '驳回'}审核 #{log_id}",
                show_alert=True
            )
        else:
            await query.answer("❌ 操作失败", show_alert=True)
            
        # 刷新页面
        # 从原始的callback_data中提取页码
        # 格式: admin:rg:{rule_group_id}:logs:pending:{page}
        try:
            current_page = int(query.data.split(":")[-2])  # 倒数第二个是页码
        except (IndexError, ValueError):
            current_page = 1  # 如果解析失败，默认第1页
        
        # 重新调用handle_pending_logs
        context.user_data["callback_query"] = query
        context.user_data["callback_data"] = f"admin:rg:{rule_group_id}:logs:pending:{current_page}"
        await self.handle_pending_logs(update, context)

    @CallbackRegistry.register(r"^admin:rg:.{16}:logs:violations:(\d+)$")
    async def handle_violations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理违规记录查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        rule_group_id = query.data.split(":")[2]
        
        # 获取规则组下的所有群组
        chats = await self.chat_service.get_chats_by_rule_group(rule_group_id)
        chat_ids = [chat.chat_id for chat in chats]
        
        # 获取违规统计
        violations = await self.user_moderation_service.get_violation_stats(chat_ids=chat_ids)
        
        if not violations:
            text = "📋 违规统计\n\n暂无违规记录"
        else:
            text = "📋 违规统计：\n\n"
            for vtype, stats in violations.items():
                text += (
                    f"类型: {vtype}\n"
                    f"总次数: {stats['count']}\n"
                    f"涉及用户数: {stats['user_count']}\n"
                    f"------------------------\n"
                )

        keyboard = [
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:logs")]
        ]
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:logs:reviews:(\d+)$")
    async def handle_reviews(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理审核记录查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return

        rule_group_id = query.data.split(":")[2]
        
        # 获取规则组下的所有群组
        chats = await self.chat_service.get_chats_by_rule_group(rule_group_id)
        chat_ids = [chat.chat_id for chat in chats]
        
        # 获取审核统计
        stats = await self.moderation_log_service.get_review_stats(chat_ids=chat_ids)
        
        if not stats:
            text = "📋 审核统计\n\n暂无审核记录"
        else:
            text = "📋 审核统计：\n\n"
            for status, stat in stats.items():
                text += (
                    f"状态: {status}\n"
                    f"数量: {stat['count']}\n"
                    f"涉及用户数: {stat['user_count']}\n"
                    f"涉及群组数: {stat['chat_count']}\n"
                    f"平均置信度: {stat['avg_confidence']:.2f}\n"
                    f"------------------------\n"
                )

        keyboard = [
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:logs")]
        ]
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @CallbackRegistry.register(r"^admin:rg:.{16}:logs:stats$")
    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理统计信息查看"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        
        # 获取规则组下的所有群组
        chats = await self.chat_service.get_chats_by_rule_group(rule_group_id)
        chat_ids = [chat.chat_id for chat in chats]
            
        # 获取各种统计信息
        review_stats = await self.moderation_log_service.get_review_stats(chat_ids=chat_ids)
        
        text = "📊 审核统计\n\n"
        
        # 审核状态统计
        text += "审核状态统计：\n"
        total_count = 0
        for status, stat in review_stats.items():
            count = stat['count']
            total_count += count
            text += f"{status}: {count} 条\n"
        text += f"总计: {total_count} 条\n\n"
        
        # AI置信度统计
        text += "AI置信度统计：\n"
        for status, stat in review_stats.items():
            text += f"{status}: {stat['avg_confidence']:.2%}\n"
        
        keyboard = [
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:logs")]
        ]
        
        await self._safe_edit_message(
            query,
            text[:4000],  # Telegram消息长度限制
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# 初始化处理器
AdminLogHandler()