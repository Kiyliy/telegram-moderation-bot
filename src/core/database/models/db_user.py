from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class UserInfo:
    """用户信息数据库模型"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    chat_id: Optional[int] = None
    user_name: Optional[str] = None
    display_name: Optional[str] = None
    is_blocked: bool = False
    daily_point_balance: int = 0
    daily_point_last_reset_at: Optional[int] = None
    vip_point_balance: int = 0
    vip_point_expired_date: Optional[int] = None
    permanent_point_balance: int = 0
    has_used_ai: bool = False
    invited_by_user_id: Optional[int] = None
    language: str = "en"  # 默认英语
    create_at: Optional[int] = None
    last_update_at: Optional[int] = None

    @classmethod
    def from_list(cls, row: list[Any]) -> "UserInfo":
        """从列表创建对象"""
        return cls(
            id=row[0],
            user_id=row[1],
            chat_id=row[2],
            user_name=row[3],
            display_name=row[4],
            is_blocked=row[5],
            daily_point_balance=row[6],
            daily_point_last_reset_at=row[7],
            vip_point_balance=row[8],
            vip_point_expired_date=row[9],
            permanent_point_balance=row[10],
            has_used_ai=row[11],
            invited_by_user_id=row[12],
            language=row[13],
            create_at=row[14],
            last_update_at=row[15]
        )

    @classmethod
    def from_dict(cls, data: dict) -> "UserInfo":
        """从字典创建对象"""
        return cls(**data)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'user_name': self.user_name,
            'display_name': self.display_name,
            'is_blocked': self.is_blocked,
            'daily_point_balance': self.daily_point_balance,
            'daily_point_last_reset_at': self.daily_point_last_reset_at,
            'vip_point_balance': self.vip_point_balance,
            'vip_point_expired_date': self.vip_point_expired_date,
            'permanent_point_balance': self.permanent_point_balance,
            'has_used_ai': self.has_used_ai,
            'invited_by_user_id': self.invited_by_user_id,
            'language': self.language,
            'create_at': self.create_at,
            'last_update_at': self.last_update_at
        }

    def __str__(self) -> str:
        return (f"UserInfo(user_id={self.user_id}, user_name={self.user_name}, "
                f"display_name={self.display_name}, is_blocked={self.is_blocked}, "
                f"daily_point_balance={self.daily_point_balance}, "
                f"daily_point_last_reset_at={self.daily_point_last_reset_at}, "
                f"vip_point_balance={self.vip_point_balance}, "
                f"vip_point_expired_date={self.vip_point_expired_date}, "
                f"permanent_point_balance={self.permanent_point_balance}, "
                f"language={self.language}, create_at={self.create_at}, "
                f"last_update_at={self.last_update_at})")