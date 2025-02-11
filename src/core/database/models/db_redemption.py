from dataclasses import dataclass
from typing import Optional


@dataclass
class RedemptionCodesInfo:
    id: Optional[int] = None
    code: Optional[str] = None
    created_at: Optional[int] = None  # Unix timestamp
    updated_at: Optional[int] = None  # Unix timestamp
    user_id: Optional[int] = None
    used_at: Optional[int] = None  # Unix timestamp
    vip_days: Optional[int] = None
    vip_points: Optional[int] = None
    permanent_point_balance: Optional[int] = None
    is_active: Optional[bool] = None
    caption: Optional[str] = None

    @classmethod
    def from_list(cls, row: list) -> "RedemptionCodesInfo":
        """从列表创建对象"""
        return cls(
            id=row[0],
            code=row[1],
            created_at=row[2],
            updated_at=row[3],
            user_id=row[4],
            used_at=row[5],
            vip_days=row[6],
            vip_points=row[7],
            permanent_point_balance=row[8],
            is_active=row[9],
            caption=row[10]
        )

    @classmethod
    def from_dict(cls, data: dict) -> "RedemptionCodesInfo":
        """从字典创建对象"""
        return cls(**data)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'user_id': self.user_id,
            'used_at': self.used_at,
            'vip_days': self.vip_days,
            'vip_points': self.vip_points,
            'permanent_point_balance': self.permanent_point_balance,
            'is_active': self.is_active,
            'caption': self.caption
        }