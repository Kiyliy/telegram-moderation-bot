import aiomysql
import traceback
from src.core.logger import logger
from typing import Optional
import os
import mysql.connector
from src.core.database.models.db_chat import ChatInfo


class ChatDatabase:
    def __init__(self) -> None:
        self.DB_CONFIG = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_APP_USER"),
            "password": os.getenv("DB_APP_USER_PASSWORD"),
            "db": os.getenv("DB_APP_NAME"),
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", 10)),
        }
        # 不是调试模式, 才创建表
        if os.getenv("DEBUG", "False") != "True":
            self.create_chats_table()

    def create_chats_table(self):
        try:
            conn = mysql.connector.connect(**self.DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    chat_id BIGINT NOT NULL UNIQUE,
                    chat_type ENUM('private', 'group', 'supergroup', 'channel') NOT NULL,
                    title VARCHAR(255),
                    owner_id BIGINT,
                    ads TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_owner_id (owner_id),
                    INDEX idx_chat_type (chat_type)
                )
            """
            )
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("Chats table created successfully.")
        except Exception as e:
            logger.error(f"Error creating chats table: {str(e)}", exc_info=True)
            print(f"Error creating chats table: {str(e)}\n{traceback.format_exc()}")

    async def add_chat(
        self, chat_id: int, chat_type: str, title: str = None, owner_id: int = None
    ) -> dict:
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO chats (chat_id, chat_type, title, owner_id) VALUES (%s, %s, %s, %s)",
                        (chat_id, chat_type, title, owner_id),
                    )
                    await conn.commit()
                    return {"success": True, "message": "Chat added successfully"}
        except Exception as e:
            logger.error(f"Error adding chat {chat_id}: {str(e)}", exc_info=True)
            print(f"Error adding chat {chat_id}: {str(e)}\n{traceback.format_exc()}")
            return {"success": False, "message": f"Error: {str(e)}"}

    async def update_chat_info(
        self, chat_id: int, chat_type: str, title: str = None
    ) -> dict:
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE chats SET chat_type = %s, title = %s WHERE chat_id = %s",
                        (chat_type, title, chat_id),
                    )
                    await conn.commit()
                    return {"success": True, "message": "Chat updated successfully"}
        except Exception as e:
            logger.error(f"Error updating chat {chat_id}: {str(e)}", exc_info=True)
            print(f"Error updating chat {chat_id}: {str(e)}\n{traceback.format_exc()}")
            return {"success": False, "message": f"Error: {str(e)}"}

    async def bind_group_to_user(self, group_id: int, user_id: int) -> dict:
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE chats SET owner_id = %s WHERE chat_id = %s",
                        (user_id, group_id),
                    )
                    await conn.commit()
                    return {"success": True, "message": "Group bound to user successfully"}
        except Exception as e:
            logger.error(f"Error binding group {group_id} to user {user_id}: {str(e)}", exc_info=True)
            print(f"Error binding group {group_id} to user {user_id}: {str(e)}\n{traceback.format_exc()}")
            return {"success": False, "message": f"Error: {str(e)}"}

    async def unbind_group_from_user(self, group_id: int, user_id: int) -> dict:
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE chats SET owner_id = %s WHERE chat_id = %s",
                        (None, group_id),
                    )
                    await conn.commit()
                    return {"success": True, "message": "Group unbound from user successfully"}
        except Exception as e:
            logger.error(f"Error unbinding group {group_id} from user {user_id}: {str(e)}", exc_info=True)
            print(f"Error unbinding group {group_id} from user {user_id}: {str(e)}\n{traceback.format_exc()}")
            return {"success": False, "message": f"Error: {str(e)}"}

    async def get_owner_groups(self, user_id: int) -> list:
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM chats WHERE owner_id = %s", (user_id,)
                    )
                    groups = await cursor.fetchall()
                    return groups
        except Exception as e:
            logger.error(f"Error fetching groups for user {user_id}: {str(e)}", exc_info=True)
            print(f"Error fetching groups for user {user_id}: {str(e)}\n{traceback.format_exc()}")

    async def update_chat_ads(self, chat_id: int, ads: str) -> dict:
        def _str_json(ads: str) -> str:
            """
            因为json不支持单引号, 所以需要将单引号转换为双引号
            """
            ads = str(ads) if ads else None
            ads_str = ads.replace("'", '"')
            return ads_str

        ads = _str_json(ads)
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE chats SET ads = %s WHERE chat_id = %s", (ads, chat_id)
                    )
                    await conn.commit()
                    return {"success": True, "message": "Chat ads updated successfully"}
        except Exception as e:
            logger.error(f"Error updating chat ads {chat_id}: {str(e)}", exc_info=True)
            print(
                f"Error updating chat ads {chat_id}: {str(e)}\n{traceback.format_exc()}"
            )
            return {"success": False, "message": f"Error: {str(e)}"}

    async def get_chats_by_owner(self, owner_id: int) -> list:
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT * FROM chats WHERE owner_id = %s", (owner_id,)
                    )
                    chats = await cursor.fetchall()
                    return chats
        except Exception as e:
            logger.error(
                f"Error fetching chats for owner {owner_id}: {str(e)}", exc_info=True
            )
            print(
                f"Error fetching chats for owner {owner_id}: {str(e)}\n{traceback.format_exc()}"
            )
            return []

    async def get_chat_info(self, chat_id: int) -> Optional[ChatInfo]:
        """
        返回 chat_info对象 或 None
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM chats WHERE chat_id = %s", (chat_id,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return ChatInfo.from_list(row)
                    else:
                        return None
        except Exception as e:
            logger.error(
                f"Error fetching chat info for chat_id {chat_id}: {str(e)}",
                exc_info=True,
            )
            print(
                f"Error fetching chat info for chat_id {chat_id}: {str(e)}\n{traceback.format_exc()}"
            )
            return None
