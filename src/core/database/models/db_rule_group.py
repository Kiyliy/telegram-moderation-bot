from typing import Optional, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class RuleGroup:
    """规则组模型"""
    id: Optional[int] = None
    rule_id: Optional[str] = None
    name: str = ""
    owner_id: int = 0
    description: Optional[str] = None
    settings: Optional[Dict] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    @classmethod
    def from_list(cls, row: list[Any]) -> "RuleGroup":
        """从数据库行创建实例"""
        if not row:
            return cls()
            
        return cls(
            id=row[0],
            rule_id=row[1],
            name=row[2],
            owner_id=row[3],
            description=row[4],
            settings=json.loads(row[5]) if row[5] else None,
            created_at=row[6],
            updated_at=row[7]
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleGroup":
        """从字典创建实例"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'name': self.name,
            'owner_id': self.owner_id,
            'description': self.description,
            'settings': self.settings,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 