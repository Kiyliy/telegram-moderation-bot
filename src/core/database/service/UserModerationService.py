from typing import Optional, List, Dict, Tuple
from src.core.database.models.db_userWarningStatus import UserWarningStatus
from src.core.database.models.db_userViolation import UserViolation
from src.core.database.models.db_moderation_log import ModerationLog
from src.core.database.service.ViolationService import ViolationService
from src.core.database.service.WarningService import WarningService
from src.core.database.service.ModerationLogService import ModerationLogService


class UserModerationService:
    """用户审核服务类"""
    
    def __init__(self):
        self.warning_service = WarningService()
        self.violation_service = ViolationService()
        self.moderation_log_service = ModerationLogService()
        
    async def record_violation(
        self,
        user_id: int,
        chat_id: int,
        violation_type: str,
        message_id: Optional[int] = None,
        content: Optional[str] = None,
        content_type: str = "text",
        operator_id: Optional[int] = None,
        is_auto: bool = True,
        confidence: Optional[float] = None
    ) -> Tuple[UserViolation, UserWarningStatus, str, Optional[int]]:
        """
        记录违规并更新警告状态
        
        Returns:
            (违规记录, 警告状态, 处罚类型, 处罚时长)
        """
        # 添加警告并获取处罚措施
        status, action, duration = await self.warning_service.add_warning(user_id, chat_id)
        
        # 记录违规
        violation = await self.violation_service.add_violation(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            violation_type=violation_type,
            content=content,
            action=action,
            duration=duration,
            operator_id=operator_id
        )
        
        # 记录审核日志
        await self.moderation_log_service.add_moderation_log(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            content=content,
            content_type=content_type,
            violation_type=violation_type,
            action=action,
            action_duration=duration,
            operator_id=operator_id,
            is_auto=is_auto,
            confidence=confidence
        )
        
        return violation, status, action, duration
        
    async def get_user_status(
        self,
        user_id: int,
        chat_id: int
    ) -> Optional[UserWarningStatus]:
        """获取用户状态"""
        return await self.warning_service.get_user_status(user_id, chat_id)
        
    async def get_user_violations(
        self,
        user_id: int,
        chat_id: Optional[int] = None,
        limit: int = 10
    ) -> List[UserViolation]:
        """获取用户违规记录"""
        return await self.violation_service.get_user_violations(user_id, chat_id, limit)
        
    async def get_chat_violations(
        self,
        chat_id: int,
        limit: int = 10
    ) -> List[UserViolation]:
        """获取群组违规记录"""
        return await self.violation_service.get_chat_violations(chat_id, limit)
        
    async def get_muted_users(
        self,
        chat_id: int
    ) -> List[UserWarningStatus]:
        """获取被禁言的用户"""
        return await self.warning_service.get_muted_users(chat_id)
        
    async def get_banned_users(
        self,
        chat_id: int
    ) -> List[UserWarningStatus]:
        """获取被封禁的用户"""
        return await self.warning_service.get_banned_users(chat_id)
        
    async def get_violation_stats(
        self,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Dict:
        """获取违规统计"""
        if chat_id:
            return await self.violation_service.get_chat_violation_stats(chat_id)
        if user_id:
            return await self.violation_service.get_user_violation_stats(user_id)
        return {}
        
    async def remove_warning(
        self,
        user_id: int,
        chat_id: int,
        count: int = 1
    ) -> Optional[UserWarningStatus]:
        """减少警告次数"""
        return await self.warning_service.remove_warning(user_id, chat_id, count)
        
    async def clear_warnings(
        self,
        user_id: int,
        chat_id: int
    ) -> Optional[UserWarningStatus]:
        """清除所有警告"""
        return await self.warning_service.clear_warnings(user_id, chat_id)
        
    async def unmute_user(
        self,
        user_id: int,
        chat_id: int
    ) -> Optional[UserWarningStatus]:
        """解除禁言"""
        return await self.warning_service.unmute_user(user_id, chat_id)
        
    async def unban_user(
        self,
        user_id: int,
        chat_id: int
    ) -> Optional[UserWarningStatus]:
        """解除封禁"""
        return await self.warning_service.unban_user(user_id, chat_id)