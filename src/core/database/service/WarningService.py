from typing import Optional, List, Dict
from src.core.database.models.db_userWarningStatus import UserWarningStatus
from src.core.database.db.UserWarningStatusDatabase import UserWarningStatusDatabase
from src.core.config.config import config
from data.ConfigKeys import ConfigKeys as configkey
import time


class WarningService:
    """用户警告服务类"""
    
    def __init__(self):
        self.warning_db = UserWarningStatusDatabase()
        self._load_settings()
        
    def _load_settings(self) -> None:
        """加载设置"""
        self.mute_durations = config.get_config(configkey.bot.settings.punishment.MUTE_DURATIONS, [300, 3600, 86400])
        self.ban_threshold = config.get_config(configkey.bot.settings.punishment.BAN_THRESHOLD, 5)
        
    def _determine_punishment(self, warning_count: int) -> tuple[str, Optional[int]]:
        """
        根据警告次数确定处罚措施
        
        Returns:
            (动作类型, 时长)
            动作类型: warn/mute/ban
            时长: 禁言时长（秒），仅在mute时有效
        """
        if warning_count >= self.ban_threshold - 1:  # 下一次就要达到封禁阈值
            return 'ban', None
            
        if warning_count == 0:  # 第一次警告
            return 'warn', None
            
        # 选择禁言时长
        duration_index = min(warning_count - 1, len(self.mute_durations) - 1)
        return 'mute', self.mute_durations[duration_index]
        
    async def get_or_create_status(
        self,
        user_id: int,
        chat_id: int
    ) -> UserWarningStatus:
        """获取或创建警告状态"""
        status = await self.warning_db.get_by_user_chat(user_id, chat_id)
        if not status:
            status = UserWarningStatus(
                user_id=user_id,
                chat_id=chat_id,
                created_at=int(time.time())
            )
            result = await self.warning_db.insert(status)
            if result:
                status.id = result
        return status
        
    async def add_warning(
        self,
        user_id: int,
        chat_id: int
    ) -> tuple[UserWarningStatus, str, Optional[int]]:
        """
        添加警告
        
        Returns:
            (警告状态, 处罚类型, 处罚时长)
        """
        status = await self.get_or_create_status(user_id, chat_id)
        
        # 确定处罚措施
        action, duration = self._determine_punishment(status.warning_count)
        
        # 更新状态
        status.warning_count += 1
        status.updated_at = int(time.time())
        
        if action == 'mute':
            status.muted_until = int(time.time()) + duration
        elif action == 'ban':
            status.banned_at = int(time.time())
            
        # 保存更新
        await self.warning_db.update(status)
        
        return status, action, duration
        
    async def remove_warning(
        self,
        user_id: int,
        chat_id: int,
        count: int = 1
    ) -> Optional[UserWarningStatus]:
        """减少警告次数"""
        status = await self.warning_db.get_by_user_chat(user_id, chat_id)
        if not status:
            return None
            
        status.warning_count = max(0, status.warning_count - count)
        status.updated_at = int(time.time())
        
        # 如果警告次数为0，清除所有处罚
        if status.warning_count == 0:
            status.muted_until = None
            status.banned_at = None
            
        await self.warning_db.update(status)
        return status
        
    async def clear_warnings(
        self,
        user_id: int,
        chat_id: int
    ) -> Optional[UserWarningStatus]:
        """清除所有警告"""
        return await self.remove_warning(user_id, chat_id, 999)
        
    async def unmute_user(
        self,
        user_id: int,
        chat_id: int
    ) -> Optional[UserWarningStatus]:
        """解除禁言"""
        status = await self.warning_db.get_by_user_chat(user_id, chat_id)
        if not status:
            return None
            
        status.muted_until = None
        status.updated_at = int(time.time())
        await self.warning_db.update(status)
        return status
        
    async def unban_user(
        self,
        user_id: int,
        chat_id: int
    ) -> Optional[UserWarningStatus]:
        """解除封禁"""
        status = await self.warning_db.get_by_user_chat(user_id, chat_id)
        if not status:
            return None
            
        status.banned_at = None
        status.warning_count = 0  # 重置警告次数
        status.updated_at = int(time.time())
        await self.warning_db.update(status)
        return status
        
    async def get_user_status(
        self,
        user_id: int,
        chat_id: int
    ) -> Optional[UserWarningStatus]:
        """获取用户状态"""
        return await self.warning_db.get_by_user_chat(user_id, chat_id)
        
    async def get_user_statuses(
        self,
        user_id: int
    ) -> List[UserWarningStatus]:
        """获取用户在所有群组的状态"""
        return await self.warning_db.get_by_user(user_id)
        
    async def get_chat_statuses(
        self,
        chat_id: int
    ) -> List[UserWarningStatus]:
        """获取群组内所有用户的状态"""
        return await self.warning_db.get_by_chat(chat_id)
        
    async def get_muted_users(
        self,
        chat_id: int
    ) -> List[UserWarningStatus]:
        """获取被禁言的用户"""
        return await self.warning_db.get_muted_users(chat_id)
        
    async def get_banned_users(
        self,
        chat_id: int
    ) -> List[UserWarningStatus]:
        """获取被封禁的用户"""
        return await self.warning_db.get_banned_users(chat_id) 