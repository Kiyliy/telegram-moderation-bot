from typing import Dict, Any, Optional, List
from src.core.database.models.db_chat import ChatInfo
from src.core.database.db.base_database import BaseDatabase
import os


class ChatDatabase(BaseDatabase):
    """群组数据库操作类"""
    
    def _initialize(self):
        super()._initialize()
        self.table_name = "chats"
        if os.getenv("SKIP_DB_INIT", "False") != "True":
            print("创建群组表...")
            self._create_table()
        else:
            print("跳过创建群组表")
        
    def _create_table(self) -> None:
        """创建表"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            chat_id BIGINT NOT NULL UNIQUE,
            chat_type ENUM('private', 'group', 'supergroup', 'channel') NOT NULL,
            title VARCHAR(255),
            owner_id BIGINT,
            rule_group_id VARCHAR(16),
            ads TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_owner_id (owner_id),
            INDEX idx_chat_type (chat_type),
            INDEX idx_rule_group (rule_group_id)
        )
        """
        self.execute(sql)

    async def add_chat(
        self,
        chat_id: int,
        chat_type: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """添加群组"""
        sql = f"""
        INSERT INTO {self.table_name} (
            chat_id, chat_type, title
        ) VALUES (%s, %s, %s)
        """
        result = await self.execute_async(sql, (chat_id, chat_type, title))
        return self.format_result(
            bool(result),
            f"Chat {chat_id} {'added' if result else 'failed to add'}"
        )

    async def update_chat_info(
        self,
        chat_id: int,
        chat_type: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新群组信息"""
        sql = f"""
        UPDATE {self.table_name} 
        SET chat_type = %s, title = %s 
        WHERE chat_id = %s
        """
        result = await self.execute_async(sql, (chat_type, title, chat_id))
        return self.format_result(
            bool(result),
            f"Chat {chat_id} {'updated' if result else 'failed to update'}"
        )
        
    async def bind_group_to_user(
        self,
        group_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """绑定群组到用户"""
        sql = f"""
        UPDATE {self.table_name} 
        SET owner_id = %s 
        WHERE chat_id = %s
        """
        result = await self.execute_async(sql, (user_id, group_id))
        return self.format_result(
            bool(result),
            f"Group {group_id} {'bound' if result else 'failed to bind'} to user {user_id}"
        )
        
    async def unbind_group_from_user(
        self,
        group_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """解绑群组"""
        sql = f"""
        UPDATE {self.table_name} 
        SET owner_id = NULL 
        WHERE chat_id = %s AND owner_id = %s
        """
        result = await self.execute_async(sql, (group_id, user_id))
        return self.format_result(
            bool(result),
            f"Group {group_id} {'unbound' if result else 'failed to unbind'} from user {user_id}"
        )
        
    async def get_owner_groups(self, user_id: int) -> List[ChatInfo]:
        """获取用户拥有的群组"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE owner_id = %s
        """
        rows = await self.fetch_all(sql, (user_id,))
        return [ChatInfo.from_list(row) for row in rows]
        
    def _str_json(self, ads: Optional[str]) -> Optional[str]:
        """将单引号转换为双引号"""
        if not ads:
            return None
        return str(ads).replace("'", '"')
        
    async def update_chat_ads(
        self,
        chat_id: int,
        ads: Optional[str]
    ) -> Dict[str, Any]:
        """更新群组广告"""
        ads = self._str_json(ads)
        sql = f"""
        UPDATE {self.table_name} 
        SET ads = %s 
        WHERE chat_id = %s
        """
        result = await self.execute_async(sql, (ads, chat_id))
        return self.format_result(
            bool(result),
            f"Chat {chat_id} ads {'updated' if result else 'failed to update'}"
        )
        
    async def get_chats_by_owner(self, owner_id: int) -> List[ChatInfo]:
        """获取用户拥有的所有群组"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE owner_id = %s
        """
        rows = await self.fetch_all_dict(sql, (owner_id,))
        return [ChatInfo.from_dict(row) for row in rows]

    async def get_chat_info(self, chat_id: int) -> Optional[ChatInfo]:
        """获取群组信息"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE chat_id = %s
        """
        row = await self.fetch_one(sql, (chat_id,))
        return ChatInfo.from_list(row) if row else None

    async def bind_chat_to_rule_group(
        self,
        chat_id: int,
        rule_group_id: int
    ) -> Dict[str, Any]:
        """绑定群组到规则组"""
        sql = f"""
        UPDATE {self.table_name} 
        SET rule_group_id = %s 
        WHERE chat_id = %s
        """
        result = await self.execute_async(sql, (rule_group_id, chat_id))
        return self.format_result(
            bool(result),
            f"Chat {chat_id} {'bound' if result else 'failed to bind'} to rule group {rule_group_id}"
        )
        
    async def unbind_chat_from_rule_group(
        self,
        chat_id: int
    ) -> Dict[str, Any]:
        """解绑群组"""
        sql = f"""
        UPDATE {self.table_name} 
        SET rule_group_id = NULL 
        WHERE chat_id = %s
        """
        result = await self.execute_async(sql, (chat_id,))
        return self.format_result(
            bool(result),
            f"Chat {chat_id} {'unbound' if result else 'failed to unbind'}"
        )
        
    async def get_chats_by_rule_group(
        self,
        rule_group_id: str
    ) -> List[ChatInfo]:
        """获取规则组内的所有群组"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE rule_group_id = %s
        ORDER BY created_at DESC
        """
        rows = await self.fetch_all(sql, (rule_group_id,))
        return [ChatInfo.from_list(row) for row in rows]
        
    async def get_unbound_chats(self, user_id) -> List[ChatInfo]:
        """获取用户所属的群组下, 所有未绑定的群组"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE rule_group_id IS NULL
        AND owner_id = %s
        ORDER BY created_at DESC
        """
        rows = await self.fetch_all(sql, (user_id,))
        return [ChatInfo.from_list(row) for row in rows]

    async def get_chat_rule_group_id(self, chat_id: int) -> str:
        """获取群组的规则组id"""
        sql = f"""
        SELECT rule_group_id FROM {self.table_name}
        WHERE chat_id = %s
        """
        row = await self.fetch_one(sql, (chat_id,))
        return row[0] if row else None