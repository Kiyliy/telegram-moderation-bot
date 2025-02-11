from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class ChatMessages:
    """聊天消息数据库模型"""
    id: Optional[int] = None
    chat_id: Optional[int] = None
    message_id: Optional[int] = None
    from_type: Optional[str] = None
    user_id: Optional[int] = None
    message_text: Optional[str] = None
    photo_url_list: Optional[str] = None
    timestamp: Optional[int] = None
    reply_to_message_id: Optional[int] = None

    @classmethod
    def from_list(cls, row: list[Any]) -> "ChatMessages":
        """从列表创建对象"""
        return cls(
            id=row[0],
            chat_id=row[1],
            message_id=row[2],
            from_type=row[3],
            user_id=row[4],
            message_text=row[5],
            photo_url_list=row[6],
            timestamp=row[7],
            reply_to_message_id=row[8] if len(row) > 8 else None
        )

    @classmethod
    def from_dict(cls, data: dict) -> "ChatMessages":
        """从字典创建对象"""
        return cls(**data)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'from_type': self.from_type,
            'user_id': self.user_id,
            'message_text': self.message_text,
            'photo_url_list': self.photo_url_list,
            'timestamp': self.timestamp,
            'reply_to_message_id': self.reply_to_message_id
        }