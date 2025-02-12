import os
import mysql.connector
from src.core.logger import logger
import aiomysql
from typing import Dict, Any, List, Union, Optional
import traceback
from src.core.database.models.db_log import UserLogsEntry
import json
from src.core.database.db.base_database import BaseDatabase


class UserLogsDatabase(BaseDatabase):
    """用户日志数据库操作类"""
    
    def _initialize(self):
        super()._initialize()
        self.table_name = "user_logs"
        if os.getenv("SKIP_DB_INIT", "False") != "True":
            print("创建用户日志表...")
            self._create_table()
        else:
            print("跳过创建用户日志表")
        
    def _create_table(self) -> None:
        """创建表"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            session_id VARCHAR(255) UNIQUE,
            user_id BIGINT NOT NULL,
            chat_id BIGINT,
            message_id BIGINT,
            log_type TEXT NOT NULL,
            user_message TEXT,
            msg_history TEXT,
            bot_response TEXT,
            caption TEXT,
            point_change JSON,
            vip_days_change INT,
            extra_data JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_chat_id (chat_id),
            INDEX idx_created_at (created_at)
        )
        """
        self.execute(sql)
        
    def _safe_json_dumps(self, data: Union[str, Dict[str, Any], None]) -> Optional[str]:
        """安全地将数据转换为JSON字符串"""
        if data is None:
            return None
        if isinstance(data, str):
            return data
        try:
            return json.dumps(data, ensure_ascii=False)
        except:
            return str(data)
        
    async def insert_logs(self, log_entries: List[UserLogsEntry]) -> Dict[str, Any]:
        """批量插入日志"""
        sql = f"""
        INSERT INTO {self.table_name} (
            user_id, chat_id, message_id, session_id, log_type, 
            user_message, msg_history, bot_response, caption, 
            point_change, vip_days_change, extra_data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = [
            (
                entry.user_id,
                entry.chat_id,
                entry.message_id,
                entry.session_id,
                self._safe_json_dumps(entry.log_type),
                self._safe_json_dumps(entry.user_message),
                self._safe_json_dumps(entry.msg_history),
                self._safe_json_dumps(entry.bot_response),
                self._safe_json_dumps(entry.caption),
                self._safe_json_dumps(entry.point_change),
                entry.vip_days_change,
                self._safe_json_dumps(entry.extra_data),
            )
            for entry in log_entries
        ]
        
        success_count = 0
        for value in values:
            result = await self.execute_async(sql, value)
            if result:
                success_count += 1
                
        return self.format_result(
            bool(success_count),
            f"Inserted {success_count} of {len(log_entries)} logs",
            {"success_count": success_count, "total": len(log_entries)}
        )
        
    async def insert_log(self, log_entry: UserLogsEntry) -> Dict[str, Any]:
        """插入单条日志"""
        sql = f"""
        INSERT INTO {self.table_name} (
            user_id, chat_id, session_id, log_type, user_message, 
            msg_history, bot_response, caption, point_change, 
            vip_days_change, extra_data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            log_entry.user_id,
            log_entry.chat_id,
            log_entry.session_id,
            log_entry.log_type,
            log_entry.user_message,
            log_entry.msg_history,
            log_entry.bot_response,
            log_entry.caption,
            self._safe_json_dumps(log_entry.point_change),
            log_entry.vip_days_change,
            self._safe_json_dumps(log_entry.extra_data),
        )
        result = await self.execute_async(sql, values)
        return self.format_result(
            bool(result),
            f"Log {'inserted' if result else 'failed to insert'}",
            {"id": result} if result else None
        )
        
    async def get_user_logs(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> List[UserLogsEntry]:
        """获取用户日志"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        rows = await self.fetch_all(sql, (user_id, limit))
        return [UserLogsEntry.from_list(row) for row in rows]
        
    async def get_chat_logs(
        self, 
        chat_id: int, 
        limit: int = 10
    ) -> List[UserLogsEntry]:
        """获取群组日志"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE chat_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        rows = await self.fetch_all(sql, (chat_id, limit))
        return [UserLogsEntry.from_list(row) for row in rows]
        
    async def get_session_logs(self, session_id: str) -> Optional[UserLogsEntry]:
        """获取会话日志"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE session_id = %s
        """
        row = await self.fetch_one(sql, (session_id,))
        return UserLogsEntry.from_list(row) if row else None
