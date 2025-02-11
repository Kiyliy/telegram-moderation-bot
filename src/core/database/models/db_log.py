from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class UserLogsEntry:
    """用户日志条目数据库模型"""
    id: Optional[int] = None
    session_id: Optional[str] = None
    user_id: Optional[int] = None
    chat_id: Optional[int] = None
    message_id: Optional[int] = None
    log_type: Optional[str] = None
    user_message: Optional[str] = None
    msg_history: Optional[str] = None
    bot_response: Optional[str] = None
    caption: Optional[str] = None
    point_change: Optional[Dict[str, int]] = None
    vip_days_change: Optional[int] = None
    extra_data: Optional[Dict[str, Any]] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    @classmethod
    def from_list(cls, row: list) -> "UserLogsEntry":
        """从列表创建对象"""
        return cls(
            id=row[0],
            session_id=row[1],
            user_id=row[2],
            chat_id=row[3],
            message_id=row[4],
            log_type=row[5],
            user_message=row[6],
            msg_history=row[7],
            bot_response=row[8],
            caption=row[9],
            point_change=row[10],
            vip_days_change=row[11],
            extra_data=row[12],
            created_at=row[13],
            updated_at=row[14]
        )

    @classmethod
    def from_dict(cls, data: dict) -> "UserLogsEntry":
        """从字典创建对象"""
        return cls(**data)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'log_type': self.log_type,
            'user_message': self.user_message,
            'msg_history': self.msg_history,
            'bot_response': self.bot_response,
            'caption': self.caption,
            'point_change': self.point_change,
            'vip_days_change': self.vip_days_change,
            'extra_data': self.extra_data,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }