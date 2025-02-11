import os
from datetime import datetime, timedelta
import mysql.connector
from dotenv import load_dotenv
import aiomysql
from src.core.logger import logger
import traceback
import ast
from src.core.database.models.db_message import ChatMessages


class ChatMessageHistory:
    def __init__(self):
        # 加载环境变量
        load_dotenv()

        # 从环境变量获取敏感信息
        self.db_host = os.getenv("DB_HOST")
        self.root_password = os.getenv("DB_ROOT_PASSWORD")
        self.app_db_user = os.getenv("DB_APP_USER")
        self.app_db_name = os.getenv("DB_APP_NAME")
        self.app_db_password = os.getenv("DB_APP_USER_PASSWORD")

        self.DB_CONFIG = {
            "host": self.db_host,
            "user": self.app_db_user,
            "password": self.app_db_password,  # 使用您之前设置的密码
            "db": self.app_db_name,
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", 10)),
        }
        # 不是调试模式, 创建表
        if os.getenv("DEBUG", "False") != "True":
            self._create_table()

    def _create_table(self):
        """
        创建chat_messages表
        索引: id
            chat_id
            message_id
        """
        try:
            with mysql.connector.connect(**self.DB_CONFIG) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INT PRIMARY KEY AUTO_INCREMENT,
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
                )
        except Exception as err:
            logger.error(f"创建表chat_message的过程中出现了错误:{err}", exc_info=True)
            print(
                f"创建表chat_messages的时候出现了一个错误{err},{traceback.format_exc()}"
            )

    async def _store_message(
        self,
        chat_id,
        message_id,
        user_id,
        from_type,
        message_text=None,
        photo_url_list=None,
        reply_to_message_id=None,
    ):
        """
        return: dict {"success": bool, message: ""}
        """
        try:
            photo_url_list = [] if photo_url_list == None else photo_url_list
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                    INSERT INTO chat_messages 
                    (chat_id, message_id, from_type, user_id, message_text,photo_url_list, reply_to_message_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    AS new_values
                    ON DUPLICATE KEY UPDATE
                    from_type = new_values.from_type, 
                    user_id = new_values.user_id, 
                    message_text = new_values.message_text, 
                    photo_url_list = new_values.photo_url_list,
                    reply_to_message_id = new_values.reply_to_message_id
                    """,
                        (
                            chat_id,
                            message_id,
                            from_type,
                            user_id,
                            message_text,
                            str(photo_url_list),
                            reply_to_message_id,
                        ),
                    )
                await conn.commit()
            return {"success": True, "message": "Message stored successfully"}
        except Exception as err:
            print(f"储存message的过程中出现了错误{err},{traceback.format_exc()}")
            logger.error(f"Error storing message: {err}", exc_info=True)
            return {"success": False, "message": str(err)}

    async def _get_chat_history(
        self, chat_id, current_message_id, limit=10, allow_photo=True
    ):
        """
        查询chat message的历史记录, 要求该message已经插入到db中
        parm: chat_id
        parm: current_message_id
        parm: limit
        return: dict
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    history = []
                    while len(history) < limit and current_message_id is not None:
                        try:
                            await cursor.execute(
                                """
                            SELECT * FROM chat_messages
                            WHERE chat_id = %s AND message_id = %s
                            """,
                                (chat_id, int(current_message_id)),
                            )
                            row: ChatMessages = await cursor.fetchone()
                            row = ChatMessages.from_list(row=row)
                            if row is None:
                                break

                            content = []
                            if row.message_text:  # message_text
                                content.append(
                                    {"type": "text", "text": row.message_text}
                                )
                            if allow_photo and ast.literal_eval(
                                row.photo_url_list
                            ):  # photo_url_list
                                photo_urls = ast.literal_eval(row.photo_url_list)
                                for url in photo_urls:
                                    content.append(
                                        {"type": "image_url", "image_url": {"url": url}}
                                    )

                            message = {
                                "role": (
                                    "user" if row.from_type == "user" else "assistant"
                                ),
                                "content": content,
                            }

                            history.append(message)
                            current_message_id = (
                                row.reply_to_message_id
                            )  # reply_to_message_id (索引更新为8)
                        except ValueError as e:
                            print(
                                f"Error processing message_id {current_message_id}: {e}"
                            )
                            logger.error(f"An error occerd{e}", exc_info=True)
                            break
                    # 反转消息
                    return list(reversed(history))
        except Exception as err:
            logger.error(f"an error occurred: {err}", exc_info=True)
            print(f"an error occurred, {err}, {traceback.format_exc()}")

    async def clean_old_messages(self, days=30):
        cutoff_date = datetime.now() - timedelta(days=days)
        async with aiomysql.connect(**self.DB_CONFIG) as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                DELETE FROM chat_messages WHERE timestamp < %s
                """,
                    (cutoff_date,),
                )
            await conn.commit()

    async def delete_message(self, chat_id, message_id):
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        DELETE FROM chat_messages WHERE chat_id = %s AND message_id = %s
                    """,
                        (chat_id, message_id),
                    )
                await conn.commit()
        except Exception as err:
            logger.error(
                f"删除消息chat_id: {chat_id},msg_id: {message_id}的时候出现了一个错误: {err}",
                exc_info=True,
            )
            print(
                f"删除消息chat_id: {chat_id}, msg_id: {message_id}的时候出现了一个错误: {traceback.format_exc()}"
            )

