from typing import Optional, List, Dict
import time
from src.core.database.models.db_userWarningStatus import UserWarningStatus
from src.core.database.models.db_userViolation import UserViolation
from src.core.database.db.UserWarningStatusDatabase import UserWarningStatusDatabase
from src.core.database.db.UserViolationDatabase import UserViolationDatabase
from src.core.config.config import config
from data.ConfigKeys import ConfigKeys as configkey


class UserModerationService:
    """用户审核服务类"""
    
    def __init__(self):
        self.warning_db = UserWarningStatusDatabase()
        self.violation_db = UserViolationDatabase()
        self._load_settings()
        
    def _load_settings(self) -> None:
        """加载设置"""
        self.mute_durations = config.get_config(configkey.bot.settings.punishment.MUTE_DURATIONS, [300, 3600, 86400])
        self.ban_threshold = config.get_config(configkey.bot.settings.punishment.BAN_THRESHOLD, 5)
        
    def record_violation(
        self,
        user_id: int,
        chat_id: int,
        violation_type: str,
        message_id: Optional[int] = None,
        content: Optional[str] = None,
        operator_id: Optional[int] = None
    ) -> tuple[UserViolation, UserWarningStatus]:
        """
        记录违规并更新警告状态
        
        Returns:
            (违规记录, 更新后的警告状态)
        """
        # 获取或创建警告状态
        status = self.warning_db.get_by_user_chat(user_id, chat_id)
        if not status:
            status = UserWarningStatus(
                user_id=user_id,
                chat_id=chat_id,
                created_at=int(time.time())
            )
            
        # 确定处罚措施
        action, duration = self._determine_punishment(status.warning_count)
        
        # 创建违规记录
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
        
        # 更新警告状态
        status.warning_count += 1
        status.updated_at = int(time.time())
        
        if action == 'mute':
            status.muted_until = int(time.time()) + duration
        elif action == 'ban':
            status.banned_at = int(time.time())
            
        # 保存到数据库
        self.violation_db.insert(violation)
        if status.id:
            self.warning_db.update(status)
        else:
            self.warning_db.insert(status)
            
        return violation, status
        
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
        
    def get_user_status(self, user_id: int, chat_id: int) -> Optional[UserWarningStatus]:
        """获取用户状态"""
        return self.warning_db.get_by_user_chat(user_id, chat_id)
        
    def get_user_violations(self, user_id: int, chat_id: Optional[int] = None, limit: int = 10) -> List[UserViolation]:
        """获取用户违规记录"""
        if chat_id:
            return self.violation_db.get_by_user_chat(user_id, chat_id, limit)
        return self.violation_db.get_by_user(user_id, limit)
        
    def get_chat_violations(self, chat_id: int, limit: int = 10) -> List[UserViolation]:
        """获取群组违规记录"""
        return self.violation_db.get_by_chat(chat_id, limit)
        
    def get_muted_users(self, chat_id: int) -> List[UserWarningStatus]:
        """获取被禁言的用户"""
        return self.warning_db.get_muted_users(chat_id)
        
    def get_banned_users(self, chat_id: int) -> List[UserWarningStatus]:
        """获取被封禁的用户"""
        return self.warning_db.get_banned_users(chat_id)
        
    def get_violation_stats(self, chat_id: Optional[int] = None, user_id: Optional[int] = None) -> Dict:
        """获取违规统计"""
        if chat_id:
            return self.violation_db.get_stats_by_chat(chat_id)
        if user_id:
            return self.violation_db.get_stats_by_user(user_id)
        return {}
        
    def remove_warning(self, user_id: int, chat_id: int, count: int = 1) -> Optional[UserWarningStatus]:
        """减少警告次数"""
        status = self.warning_db.get_by_user_chat(user_id, chat_id)
        if not status:
            return None
            
        status.warning_count = max(0, status.warning_count - count)
        status.updated_at = int(time.time())
        
        # 如果警告次数为0，清除所有处罚
        if status.warning_count == 0:
            status.muted_until = None
            status.banned_at = None
            
        self.warning_db.update(status)
        return status
        
    def clear_warnings(self, user_id: int, chat_id: int) -> Optional[UserWarningStatus]:
        """清除所有警告"""
        return self.remove_warning(user_id, chat_id, 999)
        
    def unmute_user(self, user_id: int, chat_id: int) -> Optional[UserWarningStatus]:
        """解除禁言"""
        status = self.warning_db.get_by_user_chat(user_id, chat_id)
        if not status:
            return None
            
        status.muted_until = None
        status.updated_at = int(time.time())
        self.warning_db.update(status)
        return status
        
    def unban_user(self, user_id: int, chat_id: int) -> Optional[UserWarningStatus]:
        """解除封禁"""
        status = self.warning_db.get_by_user_chat(user_id, chat_id)
        if not status:
            return None
            
        status.banned_at = None
        status.warning_count = 0  # 重置警告次数
        status.updated_at = int(time.time())
        self.warning_db.update(status)
        return status