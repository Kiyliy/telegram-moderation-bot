from typing import Optional, List, Dict, Any
from src.core.database.models.db_rule_group import RuleGroup
from src.core.database.db.base_database import BaseDatabase
import os
import json
import uuid
import string
import random


class RuleGroupDatabase(BaseDatabase):
    """规则组数据库操作类"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "rule_group"
        if os.getenv("SKIP_DB_INIT", "False") != "True":
            print("创建规则组表...")
            self._create_table()
        else:
            print("跳过创建规则组表")
        
    def _generate_rule_id(self) -> str:
        """生成16位随机字符串作为rule_id"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(16))
        
    def _create_table(self) -> None:
        """创建表"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            rule_id VARCHAR(16) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            owner_id BIGINT NOT NULL,
            description TEXT,
            settings JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_owner (owner_id)
        )
        """
        self.execute(sql)
        
    async def create_rule_group(
        self,
        name: str,
        owner_id: int,
        description: str = None,
        settings: Dict = None
    ) -> Optional[str]:
        """创建规则组，返回rule_id"""
        rule_id = self._generate_rule_id()
        sql = f"""
        INSERT INTO {self.table_name} (
            rule_id, name, owner_id, description, settings
        ) VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            rule_id,
            name,
            owner_id,
            description,
            json.dumps(settings) if settings else None
        )
        result = await self.execute_async(sql, values)
        return rule_id if result else None
        
    async def update_rule_group(
        self,
        rule_id: str,
        name: str = None,
        description: str = None,
        settings: Dict = None
    ) -> bool:
        """更新规则组"""
        update_fields = []
        values = []
        
        if name is not None:
            update_fields.append("name = %s")
            values.append(name)
        if description is not None:
            update_fields.append("description = %s")
            values.append(description)
        if settings is not None:
            update_fields.append("settings = %s")
            values.append(json.dumps(settings))
            
        if not update_fields:
            return False
            
        sql = f"""
        UPDATE {self.table_name}
        SET {", ".join(update_fields)}
        WHERE rule_id = %s
        """
        values.append(rule_id)
        result = await self.execute_async(sql, tuple(values))
        return bool(result)
        
    async def get_rule_group(self, rule_id: str) -> Optional[RuleGroup]:
        """获取规则组信息"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE rule_id = %s
        """
        row = await self.fetch_one(sql, (rule_id,))
        return RuleGroup.from_list(row) if row else None
        
    async def get_owner_rule_groups(self, owner_id: int) -> List[RuleGroup]:
        """获取管理员的所有规则组"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE owner_id = %s
        ORDER BY created_at DESC
        """
        rows = await self.fetch_all(sql, (owner_id,))
        return [RuleGroup.from_list(row) for row in rows]
        
    async def delete_rule_group(self, rule_id: str) -> bool:
        """删除规则组"""
        sql = f"""
        DELETE FROM {self.table_name}
        WHERE rule_id = %s
        """
        result = await self.execute_async(sql, (rule_id,))
        return bool(result)
        
    async def get_rule_group_settings(self, rule_id: str) -> Optional[Dict]:
        """获取规则组设置"""
        sql = f"""
        SELECT settings FROM {self.table_name}
        WHERE rule_id = %s
        """
        row = await self.fetch_one(sql, (rule_id,))
        if not row or not row[0]:
            return None
        return json.loads(row[0]) 