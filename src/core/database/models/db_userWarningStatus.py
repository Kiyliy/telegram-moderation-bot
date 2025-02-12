from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class UserWarningStatus:
    """用户警告状态"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    chat_id: Optional[int] = None
    warning_count: int = 0  # 当前警告次数
    muted_until: Optional[int] = None  # 禁言到期时间
    banned_at: Optional[int] = None  # 封禁时间
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    @classmethod
    def from_list(cls, row: list[Any]) -> "UserWarningStatus":
        return cls(
            id=row[0],
            user_id=row[1],
            chat_id=row[2],
            warning_count=row[3],
            muted_until=row[4],
            banned_at=row[5],
            created_at=row[6],
            updated_at=row[7]
        )

    @classmethod
    def from_dict(cls, data: dict) -> "UserWarningStatus":
        return cls(**data)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'warning_count': self.warning_count,
            'muted_until': self.muted_until,
            'banned_at': self.banned_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }