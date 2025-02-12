from typing import Optional, List, Dict
from src.core.database.models.db_userViolation import UserViolation
from src.core.database.db.base_database import BaseDatabase
import os


class UserViolationDatabase(BaseDatabase):
    """用户违规记录数据库操作类"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "user_violation"
        if os.getenv("SKIP_DB_INIT", "False") != "True":
            print("创建用户违规记录表")
            self._create_table()
        else:
            print("跳过创建用户违规记录表")
        
    def _create_table(self) -> None:
        """创建表"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            message_id INTEGER,
            violation_type VARCHAR(50) NOT NULL,
            content TEXT,
            action VARCHAR(20) NOT NULL,
            duration INTEGER,
            operator_id INTEGER,
            created_at INTEGER,
            INDEX idx_user_chat (user_id, chat_id),
            INDEX idx_created_at (created_at)
        )
        """
        self.execute(sql)
        
    async def insert(self, violation: UserViolation) -> Optional[int]:
        """插入记录"""
        sql = f"""
        INSERT INTO {self.table_name} (
            user_id, chat_id, message_id, violation_type, content,
            action, duration, operator_id, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            violation.user_id,
            violation.chat_id,
            violation.message_id,
            violation.violation_type,
            violation.content,
            violation.action,
            violation.duration,
            violation.operator_id,
            violation.created_at
        )
        return await self.execute_async(sql, values)
        
    async def get_by_user_chat(self, user_id: int, chat_id: int, limit: int = 10) -> List[UserViolation]:
        """获取用户在特定群组的违规记录"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE user_id = %s AND chat_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        rows = await self.fetch_all(sql, (user_id, chat_id, limit))
        return [UserViolation.from_list(row) for row in rows]
        
    async def get_by_user(self, user_id: int, limit: int = 10) -> List[UserViolation]:
        """获取用户的所有违规记录"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        rows = await self.fetch_all(sql, (user_id, limit))
        return [UserViolation.from_list(row) for row in rows]
        
    async def get_by_chat(self, chat_id: int, limit: int = 10) -> List[UserViolation]:
        """获取群组的所有违规记录"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE chat_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        rows = await self.fetch_all(sql, (chat_id, limit))
        return [UserViolation.from_list(row) for row in rows]
        
    async def get_by_type(self, violation_type: str, limit: int = 10) -> List[UserViolation]:
        """获取特定类型的违规记录"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE violation_type = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        rows = await self.fetch_all(sql, (violation_type, limit))
        return [UserViolation.from_list(row) for row in rows]
        
    async def get_stats_by_chat(self, chat_id: int) -> Dict:
        """获取群组的违规统计"""
        sql = f"""
        SELECT 
            violation_type,
            COUNT(*) as count,
            COUNT(DISTINCT user_id) as user_count
        FROM {self.table_name}
        WHERE chat_id = %s
        GROUP BY violation_type
        """
        rows = await self.fetch_all(sql, (chat_id,))
        return {
            row[0]: {
                'count': row[1],
                'user_count': row[2]
            } for row in rows
        }
        
    async def get_stats_by_user(self, user_id: int) -> Dict:
        """获取用户的违规统计"""
        sql = f"""
        SELECT 
            violation_type,
            COUNT(*) as count,
            COUNT(DISTINCT chat_id) as chat_count
        FROM {self.table_name}
        WHERE user_id = %s
        GROUP BY violation_type
        """
        rows = await self.fetch_all(sql, (user_id,))
        return {
            row[0]: {
                'count': row[1],
                'chat_count': row[2]
            } for row in rows
        }