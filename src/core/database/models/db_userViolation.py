from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class UserViolation:
    """用户违规记录"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    chat_id: Optional[int] = None
    message_id: Optional[int] = None
    violation_type: Optional[str] = None  # nsfw/spam/violence/political
    content: Optional[str] = None  # 违规内容
    action: Optional[str] = None  # delete/warn/mute/ban
    duration: Optional[int] = None  # 处理时长（秒）
    operator_id: Optional[int] = None  # 操作者ID（机器人或管理员）
    created_at: Optional[int] = None

    @classmethod
    def from_list(cls, row: list[Any]) -> "UserViolation":
        return cls(
            id=row[0],
            user_id=row[1],
            chat_id=row[2],
            message_id=row[3],
            violation_type=row[4],
            content=row[5],
            action=row[6],
            duration=row[7],
            operator_id=row[8],
            created_at=row[9]
        )

    @classmethod
    def from_dict(cls, data: dict) -> "UserViolation":
        return cls(**data)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'violation_type': self.violation_type,
            'content': self.content,
            'action': self.action,
            'duration': self.duration,
            'operator_id': self.operator_id,
            'created_at': self.created_at
        }