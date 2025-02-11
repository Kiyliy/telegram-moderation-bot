import datetime
import os
import time
from src.core.logger import logger
import mysql.connector
from dotenv import load_dotenv
import aiomysql
from typing import Dict, Any, Optional
import traceback
from src.core.database.models.db_user import UserInfo


class UserDatabase:
    def __init__(self) -> None:
        # 从环境变量获取敏感信息
        load_dotenv()
        self.db_host = os.getenv("DB_HOST")
        self.root_password = os.getenv("DB_ROOT_PASSWORD")
        self.app_db_user = os.getenv("DB_APP_USER")
        self.app_db_name = os.getenv("DB_APP_NAME")
        self.app_db_password = os.getenv("DB_APP_USER_PASSWORD")
        self.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", 10))

        self.DB_CONFIG = {
            "host": self.db_host,
            "user": self.app_db_user,
            "password": self.app_db_password,  # 使用您之前设置的密码
            "db": self.app_db_name,
            "connect_timeout": self.connect_timeout,
        }

        if os.getenv("DEBUG", "False") != "True":
            self._create_table()

    def _create_table(self):
        """
        创建表
        索引: id
              user_id
        """
        try:
            with mysql.connector.connect(**self.DB_CONFIG) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        user_id BIGINT UNIQUE NOT NULL,
                        chat_id BIGINT,
                        user_name TEXT,
                        display_name TEXT,
                        is_blocked BOOL NOT NULL DEFAULT false,
                        daily_point_balance INT NOT NULL DEFAULT 0,
                        daily_point_last_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        vip_point_balance INT NOT NULL DEFAULT 0,
                        vip_point_expired_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        permanent_point_balance INT NOT NULL DEFAULT 0,
                        has_used_ai  BOOL NOT NULL DEFAULT false,
                        invited_by_user_id BIGINT,
                        language VARCHAR(10) NOT NULL DEFAULT 'en',
                        create_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        last_update_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_chat_id (chat_id),
                        INDEX idx_create_at (create_at),
                        INDEX idx_last_update_at (last_update_at)
                    );
                    """
                )
                conn.commit()
        except Exception as err:
            logger.error(
                f"An error occurred when try to create the table users, {err}",
                exc_info=True,
            )
            print(
                f"an error occurred when try to table users: {traceback.format_exc()}"
            )

    async def add_user(
        self,
        user_id: int,
        user_name: str,
        display_name: str,
        chat_id: Optional[int] = None,
        invited_by_user_id: Optional[int] = None,
    ) -> dict:
        """
        添加用户, 包括user_id, user_name, display_name, chat_id, permanent_point_balance 字段，其余都为默认值

        :param user_id: 用户ID
        :param user_name: 用户名
        :param display_name: 显示名
        :param chat_id: 聊天ID (可选)
        :return: {"success": bool, "message": str}
        """
        daily_points = self.config.get_daily_points()
        permanent_points = self.config.get_default_permanent_points()
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    # 如果用户不存在, 则插入新用户
                    await cursor.execute(
                        """
                        INSERT INTO users (user_id, user_name, display_name, daily_point_balance, chat_id, permanent_point_balance, invited_by_user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            user_id,
                            user_name,
                            display_name,
                            daily_points,
                            chat_id,
                            permanent_points,
                            invited_by_user_id,
                        ),
                    )
                    await conn.commit()
            return {
                "success": True,
                "message": f"User {user_id} added to database successfully",
            }
        except Exception as err:
            logger.error(
                f"An error occurred when try to add a user, {err}", exc_info=True
            )
            print(f"an error occurred when try to add a user: {traceback.format_exc()}")
            return {"success": False, "message": f"Unexpected error: {str(err)}"}

    async def get_user_info(self, user_id) -> UserInfo | None:
        """
        获取用户信息

        :param user_id: 要查询的用户ID
        :return: 如果找到用户则返回UserInfo对象,否则返回None
        :raises DatabaseError: 当数据库操作出错时
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT id,
                            user_id,
                            chat_id,
                            user_name,
                            display_name,
                            is_blocked,
                            daily_point_balance,
                            UNIX_TIMESTAMP(daily_point_last_reset_at) AS daily_point_last_reset_at,
                            vip_point_balance,
                            UNIX_TIMESTAMP(vip_point_expired_date) AS vip_point_expired_date,
                            permanent_point_balance,
                            has_used_ai,
                            invited_by_user_id,
                            language,
                            UNIX_TIMESTAMP(create_at) AS create_at,
                            UNIX_TIMESTAMP(last_update_at) AS last_update_at
                        FROM users WHERE user_id = %s;
                        """,
                        (user_id,),
                    )
                    row = await cursor.fetchone()
                    if row:
                        info: UserInfo = UserInfo.from_list(row)
                        return info
                    return None
        except Exception as err:
            logger.error(
                f"An error occurred when try to get the user info{user_id}, {err}",
                exc_info=True,
            )
            print(
                f"an error occurred when try to get the user info:{user_id} {traceback.format_exc()}"
            )

    async def update_user_disply_info(
        self, user_id: int, user_name: str, display_name: str
    ) -> bool | str:
        """
        更新用户的username, display_name
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE users SET user_name = %s, display_name = %s WHERE user_id = %s",
                        (user_name, display_name, user_id),
                    )
                    await conn.commit()
                    return {
                        "success": True,
                        "message": f"User {user_id} display info updated successfully",
                    }
        except Exception as err:
            logger.error(
                f"An error occurred when try to update the user display info: id{user_id} , {err}",
                exc_info=True,
            )
            print(
                f"an error occurred when try to update the user display info: id{user_id} {traceback.format_exc()}"
            )
            return {"success": False, "message": f"Unexpected error: {str(err)}"}

    async def update_user_ai_status(
        self, user_id: int, has_used_ai: bool
    ) -> bool | str:
        """
        更新用户的AI使用状态
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE users SET has_used_ai = %s WHERE user_id = %s",
                        (has_used_ai, user_id),
                    )
                    await conn.commit()
                    return {
                        "success": True,
                        "message": f"User {user_id} ai status updated successfully",
                    }
        except Exception as err:
            logger.error(
                f"An error occurred when try to update the user ai status: id{user_id} , {err}",
                exc_info=True,
            )
            print(
                f"an error occurred when try to update the user ai status: id{user_id} {traceback.format_exc()}"
            )
            return {"success": False, "message": f"Unexpected error: {str(err)}"}

    async def add_invited_by_user_id(
        self, user_id: int, invited_by_user_id: int
    ) -> bool | str:
        """
        异步增加用户的邀请者ID
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE users SET invited_by_user_id = %s WHERE user_id = %s",
                        (invited_by_user_id, user_id),
                    )
                    await conn.commit()
                    return {
                        "success": True,
                        "message": f"User {user_id} invited by user {invited_by_user_id} updated successfully",
                    }
        except Exception as err:
            logger.error(
                f"An error occurred when try to add the invited by user id: {err}",
                exc_info=True,
            )
            print(
                f"an error occurred when try to add the invited by user id: {traceback.format_exc()}"
            )
            return {"success": False, "message": f"Unexpected error: {str(err)}"}

    async def set_banlance(
        self,
        user_id: int,
        daily_points: int,
        vip_points: int,
        vip_expired_date: int,
        permanent_points: int,
    ) -> bool | str:
        """
        修改用户的积分 -> 充值或者消费
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        UPDATE users 
                        SET 
                            daily_point_balance = %s,
                            vip_point_balance = %s,
                            vip_point_expired_date = FROM_UNIXTIME(%s),
                            permanent_point_balance = %s
                        WHERE user_id = %s
                        """,
                        (
                            daily_points,
                            vip_points,
                            vip_expired_date,
                            permanent_points,
                            user_id,
                        ),
                    )
                    await conn.commit()
                    return {
                        "success": True,
                        "message": f"User {user_id} balance updated successfully",
                    }
        except Exception as err:
            logger.error(
                f"An error occurred when try to change the user balance: id{user_id} , {err}",
                exc_info=True,
            )
            print(
                f"an error occurred when try to change the user balance: id{user_id} {traceback.format_exc()}"
            )
            return {"success": False, "message": f"Unexpected error: {str(err)}"}

    async def reset_daily_balance(
        self, user_id: int, amount: int = 0
    ) -> Dict[str, Any]:
        """
        检查最后重置时间，如果需要则重置每日积分

        :param user_id: The ID of the user
        :param amount: The amount to set as the new daily balance (default is 0)
        :return: A dictionary with keys "success" (bool), 'message' (str), and 'reset' (bool)
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    # Get the last reset timestamp
                    await cursor.execute(
                        "SELECT UNIX_TIMESTAMP(daily_point_last_reset_at) FROM users WHERE user_id = %s",
                        (user_id,),
                    )
                    row = await cursor.fetchone()
                    # user dose not exists
                    if not row:
                        logger.error(
                            f"user {user_id} dose not exist when try to reset user's daily points"
                        )
                        print(
                            f"user {user_id} dose not exist when try to reset user's daily points"
                        )
                        return {
                            "success": False,
                            "message": f"User with ID {user_id} not found",
                            "reset": False,
                        }

                    last_reset_timestamp: int = int(row[0])

                    # Check if it's been more than 18 hours since the last reset
                    now = int(time.time())
                    time_difference = now - last_reset_timestamp

                    print(
                        f"Time since last reset: {datetime.timedelta(seconds=time_difference)}"
                    )

                    if time_difference > 18 * 3600:
                        # Reset daily balance and update last reset time
                        await cursor.execute(
                            """
                            UPDATE users 
                            SET daily_point_balance = %s, 
                                daily_point_last_reset_at = FROM_UNIXTIME(%s)
                            WHERE user_id = %s
                            """,
                            (amount, now, user_id),
                        )
                        await conn.commit()
                        return {
                            "success": True,
                            "message": f"Daily balance for user {user_id} reset to {amount}",
                            "reset": True,
                        }
                    else:
                        return {
                            "success": True,
                            "message": f"Daily balance for user {user_id} not reset (last reset was {datetime.timedelta(seconds=time_difference)} ago)",
                            "reset": False,
                        }
        except aiomysql.Error as err:
            logger.error(
                f"An error occurred when try to reset {user_id}'s daily points, {err}",
                exc_info=True,
            )
            print(
                f"an error occurred when try to reset {user_id}'s daily points: {traceback.format_exc()}"
            )
            return {
                "success": False,
                "message": f"Database error: {str(err)}",
                "reset": False,
            }
        except Exception as err:
            logger.error(
                f"An error occurred when try to reset {user_id}'s daily points, {err}",
                exc_info=True,
            )
            print(
                f"an error occurred when try to reset {user_id}'s daily points: {traceback.format_exc()}"
            )
            return {
                "success": False,
                "message": f"Unexpected error: {str(err)}",
                "reset": False,
            }

    async def get_user_language(self, user_id: int):
        '''
        获取用户的语言设置
        '''
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT language
                        FROM users
                        WHERE user_id = %s
                        """,
                        (user_id,),
                    )
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
                    return None
        except Exception as e:
            print(f"[DEBUG]: error getting user language: {str(e)}")
            logger.error(f"Error getting user language: {str(e)}")
            return None

    async def update_user_language(self, user_id: int, language: str):
        """
        更新用户的语言设置

        :param user_id: 用户ID
        :param language: 语言代码 (如 'zh_CN' 或 'en_US')
        :return: {"success": bool, "message": str}
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        UPDATE users 
                        SET language = %s
                        WHERE user_id = %s
                        """,
                        (language, user_id),
                    )
                    await conn.commit()
                    return {"success": True, "message": "Language updated successfully"}
        except Exception as e:
            logger.error(f"Error updating user language: {str(e)}")
            return {"success": False, "message": str(e)}
