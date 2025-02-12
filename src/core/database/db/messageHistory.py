from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import ast
from src.core.database.models.db_message import ChatMessages
from src.core.database.db.base_database import BaseDatabase
import os


class ChatMessageHistory(BaseDatabase):
    """聊天消息历史记录数据库操作类"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "chat_messages"
        if os.getenv("SKIP_DB_INIT", "False") != "True":
            print("创建聊天消息历史记录表...")
            self._create_table()
        else:
            print("跳过创建聊天消息历史记录表")
        
    def _create_table(self) -> None:
        """创建表"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            chat_id BIGINT NOT NULL,
            message_id BIGINT,
            from_type ENUM('user', 'bot') NOT NULL,
            user_id BIGINT,
            message_text TEXT,
            photo_url_list TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            reply_to_message_id BIGINT,
            UNIQUE(chat_id, message_id),
            INDEX idx_chat_timestamp (chat_id, timestamp)
        )
        """
        self.execute(sql)
        
    async def store_message(
        self,
        chat_id: int,
        message_id: int,
        user_id: int,
        from_type: str,
        message_text: Optional[str] = None,
        photo_url_list: Optional[List[str]] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """存储消息"""
        photo_url_list = photo_url_list or []
        sql = f"""
        INSERT INTO {self.table_name} 
        (chat_id, message_id, from_type, user_id, message_text, photo_url_list, reply_to_message_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        AS new_values
        ON DUPLICATE KEY UPDATE
        from_type = new_values.from_type, 
        user_id = new_values.user_id, 
        message_text = new_values.message_text, 
        photo_url_list = new_values.photo_url_list,
        reply_to_message_id = new_values.reply_to_message_id
        """
        values = (
            chat_id,
            message_id,
            from_type,
            user_id,
            message_text,
            str(photo_url_list),
            reply_to_message_id,
        )
        result = await self.execute_async(sql, values)
        return self.format_result(
            bool(result),
            f"Message {message_id} {'stored' if result else 'failed to store'}"
        )
        
    async def get_chat_history(
        self, 
        chat_id: int, 
        current_message_id: int, 
        limit: int = 10,
        allow_photo: bool = True
    ) -> List[Dict[str, Any]]:
        """获取聊天历史记录"""
        history = []
        while len(history) < limit and current_message_id is not None:
            sql = f"""
            SELECT * FROM {self.table_name}
            WHERE chat_id = %s AND message_id = %s
            """
            row = await self.fetch_one(sql, (chat_id, current_message_id))
            if not row:
                break
                
            message = ChatMessages.from_list(row)
            content = []
            
            if message.message_text:
                content.append({"type": "text", "text": message.message_text})
                
            if allow_photo and message.photo_url_list:
                photo_urls = ast.literal_eval(message.photo_url_list)
                for url in photo_urls:
                    content.append({"type": "image_url", "image_url": {"url": url}})
                    
            history.append({
                "role": "user" if message.from_type == "user" else "assistant",
                "content": content
            })
            
            current_message_id = message.reply_to_message_id
            
        return list(reversed(history))
        
    async def clean_old_messages(self, days: int = 30) -> Dict[str, Any]:
        """清理旧消息"""
        cutoff_date = datetime.now() - timedelta(days=days)
        sql = f"""
        DELETE FROM {self.table_name} 
        WHERE timestamp < %s
        """
        result = await self.execute_async(sql, (cutoff_date,))
        return self.format_result(
            bool(result),
            f"Old messages {'cleaned' if result else 'failed to clean'}"
        )
        
    async def delete_message(
        self, 
        chat_id: int, 
        message_id: int
    ) -> Dict[str, Any]:
        """删除消息"""
        sql = f"""
        DELETE FROM {self.table_name} 
        WHERE chat_id = %s AND message_id = %s
        """
        result = await self.execute_async(sql, (chat_id, message_id))
        return self.format_result(
            bool(result),
            f"Message {message_id} {'deleted' if result else 'failed to delete'}"
        )

