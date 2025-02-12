from typing import Optional, List
from src.core.database.models.db_userWarningStatus import UserWarningStatus
from src.core.database.db.base_database import BaseDatabase
import os


class UserWarningStatusDatabase(BaseDatabase):
    """用户警告状态数据库操作类"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "user_warning_status"
        if os.getenv("SKIP_DB_INIT", "False") != "True":
            self._create_table()
        
    def _create_table(self) -> None:
        """创建表"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            warning_count INTEGER DEFAULT 0,
            muted_until INTEGER,
            banned_at INTEGER,
            created_at INTEGER,
            updated_at INTEGER
        )
        """
        self.execute(sql)
        
    async def insert(self, status: UserWarningStatus) -> Optional[int]:
        """插入记录"""
        sql = f"""
        INSERT INTO {self.table_name} (
            user_id, chat_id, warning_count, muted_until, banned_at, 
            created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            status.user_id,
            status.chat_id,
            status.warning_count,
            status.muted_until,
            status.banned_at,
            status.created_at,
            status.updated_at
        )
        return await self.execute_async(sql, values)
        
    async def update(self, status: UserWarningStatus) -> bool:
        """更新记录"""
        sql = f"""
        UPDATE {self.table_name} SET
            warning_count = %s,
            muted_until = %s,
            banned_at = %s,
            updated_at = %s
        WHERE user_id = %s AND chat_id = %s
        """
        values = (
            status.warning_count,
            status.muted_until,
            status.banned_at,
            status.updated_at,
            status.user_id,
            status.chat_id
        )
        result = await self.execute_async(sql, values)
        return bool(result)
        
    async def get_by_user_chat(self, user_id: int, chat_id: int) -> Optional[UserWarningStatus]:
        """获取用户在特定群组的警告状态"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE user_id = %s AND chat_id = %s
        """
        row = await self.fetch_one(sql, (user_id, chat_id))
        return UserWarningStatus.from_list(row) if row else None
        
    async def get_by_user(self, user_id: int) -> List[UserWarningStatus]:
        """获取用户在所有群组的警告状态"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE user_id = %s
        """
        rows = await self.fetch_all(sql, (user_id,))
        return [UserWarningStatus.from_list(row) for row in rows]
        
    async def get_by_chat(self, chat_id: int) -> List[UserWarningStatus]:
        """获取群组内所有用户的警告状态"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE chat_id = %s
        """
        rows = await self.fetch_all(sql, (chat_id,))
        return [UserWarningStatus.from_list(row) for row in rows]
        
    async def get_muted_users(self, chat_id: int) -> List[UserWarningStatus]:
        """获取群组内当前被禁言的用户"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE chat_id = %s AND muted_until > UNIX_TIMESTAMP()
        """
        rows = await self.fetch_all(sql, (chat_id,))
        return [UserWarningStatus.from_list(row) for row in rows]
        
    async def get_banned_users(self, chat_id: int) -> List[UserWarningStatus]:
        """获取群组内被封禁的用户"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE chat_id = %s AND banned_at IS NOT NULL
        """
        rows = await self.fetch_all(sql, (chat_id,))
        return [UserWarningStatus.from_list(row) for row in rows] 
 