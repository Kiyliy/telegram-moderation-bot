from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class ModerationLog:
    """审核日志"""
    id: Optional[int] = None
    user_id: Optional[int] = None  # 被审核的用户
    chat_id: Optional[int] = None  # 群组ID
    message_id: Optional[int] = None  # 消息ID
    content: Optional[str] = None  # 审核内容
    content_type: Optional[str] = None  # 内容类型(text/image/video等)
    violation_type: Optional[str] = None  # 违规类型(nsfw/spam/violence/political)
    action: Optional[str] = None  # 处理动作(delete/warn/mute/ban)
    action_duration: Optional[int] = None  # 处理时长(秒)
    operator_id: Optional[int] = None  # 操作者ID(机器人或管理员)
    is_auto: bool = True  # 是否自动处理
    confidence: Optional[float] = None  # AI判断的置信度
    has_appeal: bool = False  # 是否有申诉
    appeal_time: Optional[int] = None  # 申诉时间
    appeal_reason: Optional[str] = None  # 申诉理由
    review_status: str = "pending"  # 人工审核状态(pending/approved/rejected)
    review_time: Optional[int] = None  # 人工审核时间
    reviewer_id: Optional[int] = None  # 审核员ID
    created_at: Optional[int] = None  # 创建时间
    updated_at: Optional[int] = None  # 更新时间

    @classmethod
    def from_list(cls, row: list[Any]) -> "ModerationLog":
        return cls(
            id=row[0],
            user_id=row[1],
            chat_id=row[2],
            message_id=row[3],
            content=row[4],
            content_type=row[5],
            violation_type=row[6],
            action=row[7],
            action_duration=row[8],
            operator_id=row[9],
            is_auto=bool(row[10]),
            confidence=row[11],
            has_appeal=bool(row[12]),
            appeal_time=row[13],
            appeal_reason=row[14],
            review_status=row[15],
            review_time=row[16],
            reviewer_id=row[17],
            created_at=row[18],
            updated_at=row[19]
        )

    @classmethod
    def from_dict(cls, data: dict) -> "ModerationLog":
        return cls(**data)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'content': self.content,
            'content_type': self.content_type,
            'violation_type': self.violation_type,
            'action': self.action,
            'action_duration': self.action_duration,
            'operator_id': self.operator_id,
            'is_auto': self.is_auto,
            'confidence': self.confidence,
            'has_appeal': self.has_appeal,
            'appeal_time': self.appeal_time,
            'appeal_reason': self.appeal_reason,
            'review_status': self.review_status,
            'review_time': self.review_time,
            'reviewer_id': self.reviewer_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 