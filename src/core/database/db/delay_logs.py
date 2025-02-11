import os
import mysql.connector
from src.core.logger import logger
import aiomysql
from typing import Dict, Any, List, Union
import traceback
from src.core.database.models.db_log import UserLogsEntry
import json


class UserLogsDatabase:
    def __init__(self, table_name: str) -> None:
        self.DB_CONFIG = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_APP_USER"),
            "password": os.getenv("DB_APP_USER_PASSWORD"),
            "db": os.getenv("DB_APP_NAME"),
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", 10)),
        }
        self.table_name = table_name
        # 不是调试模式, 才创建表
        if os.getenv("DEBUG", "False") != "True":
            self._create_table()

    def _create_table(self):
        """
        创建表
        """
        try:
            with mysql.connector.connect(**self.DB_CONFIG) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"""
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
                    )
                conn.commit()
        except Exception as err:
            logger.error(
                f"An error occurred while creating table: {err}", exc_info=True
            )
            print(f"An error occurred while creating table: {traceback.format_exc()}")

    async def insert_logs(self, log_entries: List[UserLogsEntry]) -> bool:
        """
        param: session_id: str
        param: user_id
        param: chat_id
        param: message_id
        param: log_type: Literal: ["消费","兑换","系统","其它","签到"]
        param: user_message
        param: msg_history
        param: bot_response
        param: caption
        param: point_change : dict
        param: vip_days_change: int
        param: extra_data: dict
        return bool
        """

        def safe_json_dumps(data: Union[str, Dict[str, Any], None]) -> Union[str, None]:
            if data is None:
                return None
            if isinstance(data, str):
                return data
            try:
                return json.dumps(data, ensure_ascii=False)
            except:
                return str(data)

        query = f"""
        INSERT INTO {self.table_name} (user_id, chat_id, message_id, session_id, log_type, user_message, msg_history, bot_response, 
                               caption, point_change, vip_days_change, extra_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cur:
                    values = [
                        (
                            entry.user_id,
                            entry.chat_id,
                            entry.message_id,
                            entry.session_id,
                            safe_json_dumps(entry.log_type),
                            safe_json_dumps(entry.user_message),
                            safe_json_dumps(entry.msg_history),
                            safe_json_dumps(entry.bot_response),
                            safe_json_dumps(entry.caption),
                            safe_json_dumps(entry.point_change),
                            entry.vip_days_change,
                            safe_json_dumps(entry.extra_data),
                        )
                        for entry in log_entries
                    ]
                    await cur.executemany(query, values)
                    await conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting logs: {str(e)}", exc_info=True)
            print(f"Error inserting logs: {traceback.format_exc()},{log_entries}")
            return False

    async def insert_log(self, log_entry: UserLogsEntry) -> int:
        query = f"""
        INSERT INTO {self.table_name} (user_id, chat_id, session_id, log_type, user_message, msg_history, bot_response, 
                               caption, point_change, vip_days_change, extra_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        query,
                        (
                            log_entry.user_id,
                            log_entry.chat_id,
                            log_entry.session_id,
                            log_entry.log_type,
                            log_entry.user_message,
                            log_entry.msg_history,
                            log_entry.bot_response,
                            log_entry.caption,
                            json.dumps(log_entry.point_change),
                            log_entry.vip_days_change,
                            json.dumps(log_entry.extra_data),
                        ),
                    )
                    await conn.commit()
                    return cur.lastrowid
        except Exception as err:
            logger.error(f"An error occurred while insert a log: {err}", exc_info=True)
            print(f"An error occurred while insert a log: {traceback.format_exc()}")
