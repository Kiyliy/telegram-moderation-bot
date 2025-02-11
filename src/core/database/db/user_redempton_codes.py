from dotenv import load_dotenv
import os
import aiomysql
from core.database.db.RedemptionCodesDatabase import RedemptionCodesDatabase
from core.database.db.UserDatabase import UserDatabase
from src.core.logger import logger
import traceback
import time


class userRedemptionCodes(RedemptionCodesDatabase, UserDatabase):
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
            "password": self.app_db_password,
            "db": self.app_db_name,
            "connect_timeout": self.connect_timeout,
        }

    async def user_use_redemptionCode(self, user_id: int, code: str) -> dict:
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await conn.begin()
                    try:
                        # 检查兑换码是否有效且未使用
                        await cursor.execute(
                            "SELECT * FROM redemption_codes WHERE code = %s AND is_active = 1",
                            (code,),
                        )
                        code_info = await cursor.fetchone()

                        if not code_info:
                            raise ValueError(f"Invalid or already used code: {code}")

                        # 标记兑换码为已使用
                        await cursor.execute(
                            "UPDATE redemption_codes SET is_active = 0, used_at = CURRENT_TIMESTAMP, user_id = %s WHERE code = %s",
                            (user_id, code),
                        )

                        # 获取用户当前的VIP信息
                        await cursor.execute(
                            "SELECT vip_point_balance, UNIX_TIMESTAMP(vip_point_expired_date) as vip_point_expired_date, permanent_point_balance FROM users WHERE user_id = %s",
                            (user_id,),
                        )
                        user_info = await cursor.fetchone()

                        if not user_info:
                            raise ValueError(f"User not found: {user_id}")

                        # 获取当前时间戳
                        now = int(time.time())

                        # 计算新的VIP信息
                        if user_info["vip_point_expired_date"] <= now:
                            # VIP已过期 -> 直接重新计算
                            new_vip_point_balance = code_info["vip_points"]
                            new_vip_point_expired_date = (
                                now + code_info["vip_days"] * 86400
                            )
                        else:
                            # VIP未过期
                            new_vip_point_balance = (
                                user_info["vip_point_balance"] + code_info["vip_points"]
                            )
                            new_vip_point_expired_date = max(
                                user_info["vip_point_expired_date"],
                                now + code_info["vip_days"] * 86400,
                            )

                        new_permanent_point_balance = (
                            user_info["permanent_point_balance"]
                            + code_info["permanent_point_balance"]
                        )

                        # 更新用户的VIP信息
                        await cursor.execute(
                            """
                            UPDATE users
                            SET vip_point_balance = %s,
                                vip_point_expired_date = FROM_UNIXTIME(%s),
                                permanent_point_balance = %s
                            WHERE user_id = %s
                            """,
                            (
                                new_vip_point_balance,
                                new_vip_point_expired_date,
                                new_permanent_point_balance,
                                user_id,
                            ),
                        )

                        # 提交事务
                        await conn.commit()
                        return {
                            "success": True,
                            "message": "Redemption code used successfully",
                        }

                    except Exception as e:
                        # 如果出现任何错误，回滚事务
                        await conn.rollback()
                        logger.error(
                            f"用户{user_id}兑换兑换码{code}失败! 操作已经回滚{e}",
                            exc_info=True,
                        )
                        print(
                            f"用户{user_id}兑换兑换码{code}失败! 操作已经回滚{e},{traceback.format_exc()}"
                        )
                        return {"success": False, "message": str(e)}

        except Exception as e:
            return {"success": False, "message": f"Database connection error: {str(e)}"}
