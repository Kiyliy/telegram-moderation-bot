from typing import Optional, List, Dict
from src.core.database.models.db_userViolation import UserViolation
from src.core.database.db.UserViolationDatabase import UserViolationDatabase
import time


class ViolationService:
    """违规记录服务类"""
    
    def __init__(self):
        self.violation_db = UserViolationDatabase()
        
    async def add_violation(
        self,
        user_id: int,
        chat_id: int,
        violation_type: str,
        action: str,
        message_id: Optional[int] = None,
        content: Optional[str] = None,
        duration: Optional[int] = None,
        operator_id: Optional[int] = None
    ) -> Optional[UserViolation]:
        """添加违规记录"""
        violation = UserViolation(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            violation_type=violation_type,
            content=content,
            action=action,
            duration=duration,
            operator_id=operator_id,
            created_at=int(time.time())
        )
        result = await self.violation_db.insert(violation)
        if result:
            violation.id = result
            return violation
        return None
        
    async def get_user_violations(
        self,
        user_id: int,
        chat_id: Optional[int] = None,
        limit: int = 10
    ) -> List[UserViolation]:
        """获取用户违规记录"""
        if chat_id:
            return await self.violation_db.get_by_user_chat(user_id, chat_id, limit)
        return await self.violation_db.get_by_user(user_id, limit)
        
    async def get_chat_violations(
        self,
        chat_id: int,
        limit: int = 10
    ) -> List[UserViolation]:
        """获取群组违规记录"""
        return await self.violation_db.get_by_chat(chat_id, limit)
        
    async def get_violations_by_type(
        self,
        violation_type: str,
        limit: int = 10
    ) -> List[UserViolation]:
        """获取特定类型的违规记录"""
        return await self.violation_db.get_by_type(violation_type, limit)
        
    async def get_user_violation_stats(self, user_id: int) -> Dict:
        """获取用户违规统计"""
        return await self.violation_db.get_stats_by_user(user_id)
        
    async def get_chat_violation_stats(self, chat_id: int) -> Dict:
        """获取群组违规统计"""
        return await self.violation_db.get_stats_by_chat(chat_id) 