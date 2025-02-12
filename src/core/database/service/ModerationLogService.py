from typing import Optional, List, Dict, Any
from src.core.database.models.db_moderation_log import ModerationLog
from src.core.database.db.ModerationLogDatabase import ModerationLogDatabase
import time


class ModerationLogService:
    """审核日志服务类"""
    
    def __init__(self):
        self.log_db = ModerationLogDatabase()
        
    async def add_moderation_log(
        self,
        user_id: int,
        chat_id: int,
        content_type: str,
        violation_type: Optional[str] = None,
        message_id: Optional[int] = None,
        content: Optional[str] = None,
        action: Optional[str] = None,
        action_duration: Optional[int] = None,
        operator_id: Optional[int] = None,
        is_auto: bool = True,
        confidence: Optional[float] = None
    ) -> Optional[int]:
        """添加审核日志"""
        log = ModerationLog(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            content=content,
            content_type=content_type,
            violation_type=violation_type,
            action=action,
            action_duration=action_duration,
            operator_id=operator_id,
            is_auto=is_auto,
            confidence=confidence,
            has_appeal=False,  # 默认无申诉
            review_status="pending",
            created_at=int(time.time()),
            updated_at=int(time.time())
        )
        return await self.log_db.add_log(log)
        
    async def update_review_status(
        self,
        log_id: int,
        review_status: str,
        reviewer_id: int
    ) -> bool:
        """更新审核状态"""
        return await self.log_db.update_review(
            log_id=log_id,
            review_status=review_status,
            reviewer_id=reviewer_id,
            review_time=int(time.time())
        )
        
    async def get_pending_logs(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[ModerationLog]:
        """获取待审核的日志"""
        return await self.log_db.get_pending_logs(limit, offset)
        
    async def get_user_logs(
        self,
        user_id: int,
        chat_id: Optional[int] = None,
        limit: int = 10
    ) -> List[ModerationLog]:
        """获取用户的审核日志"""
        return await self.log_db.get_logs_by_user(user_id, chat_id, limit)
        
    async def get_chat_logs(
        self,
        chat_id: int,
        limit: int = 10
    ) -> List[ModerationLog]:
        """获取群组的审核日志"""
        return await self.log_db.get_logs_by_chat(chat_id, limit)
        
    async def get_logs_by_type(
        self,
        violation_type: str,
        limit: int = 10
    ) -> List[ModerationLog]:
        """获取特定类型的审核日志"""
        return await self.log_db.get_logs_by_type(violation_type, limit)
        
    async def get_review_stats(self) -> Dict[str, Any]:
        """获取审核统计"""
        return await self.log_db.get_review_stats()
        
    async def add_appeal(
        self,
        log_id: int,
        appeal_reason: str
    ) -> bool:
        """添加申诉"""
        return await self.log_db.update_appeal(
            log_id=log_id,
            appeal_reason=appeal_reason,
            appeal_time=int(time.time())
        )
        
    async def get_pending_appeals(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[ModerationLog]:
        """获取待处理的申诉"""
        return await self.log_db.get_pending_appeals(limit, offset) 