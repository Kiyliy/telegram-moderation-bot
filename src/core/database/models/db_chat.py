from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional


class ChatType(Enum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


@dataclass
class ChatInfo:
    """聊天信息数据库模型"""
    id: Optional[int] = None
    chat_id: Optional[int] = None
    chat_type: Optional[ChatType] = None
    title: Optional[str] = None
    owner_id: Optional[int] = None
    ads: Optional[dict] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    @classmethod
    def from_list(cls, row: list[Any]) -> "ChatInfo":
        """从列表创建对象"""
        return cls(
            id=row[0],
            chat_id=row[1],
            chat_type=ChatType(row[2]) if row[2] else None,
            title=row[3],
            owner_id=row[4],
            ads=row[5],
            created_at=row[6],
            updated_at=row[7]
        )

    @classmethod
    def from_dict(cls, data: dict) -> "ChatInfo":
        """从字典创建对象"""
        # 特殊处理 chat_type 字段
        if "chat_type" in data and data["chat_type"] is not None:
            if isinstance(data["chat_type"], ChatType):
                pass  # 已经是 ChatType 类型
            elif isinstance(data["chat_type"], str):
                data["chat_type"] = ChatType(data["chat_type"])
        return cls(**data)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'chat_type': self.chat_type.value if self.chat_type else None,
            'title': self.title,
            'owner_id': self.owner_id,
            'ads': self.ads,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def __str__(self) -> str:
        return (f"ChatInfo(id={self.id}, chat_id={self.chat_id}, "
                f"chat_type={self.chat_type}, title={self.title}, "
                f"owner_id={self.owner_id}, ads={self.ads}, "
                f"created_at={self.created_at}, updated_at={self.updated_at})")
