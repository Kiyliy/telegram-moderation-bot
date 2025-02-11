import os
import time
import uuid
import aiomysql
import mysql.connector
from src.core.logger import logger
from src.core.database.models.db_redemption import RedemptionCodesInfo
import traceback

class RedemptionCodesDatabase:
    def __init__(self) -> None:
        self.DB_CONFIG = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_APP_USER"),
            "password": os.getenv("DB_APP_USER_PASSWORD"),
            "db": os.getenv("DB_APP_NAME"),
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", 10)),
        }
        if os.getenv("DEBUG", "False") != "True":
            self.create_table()

    async def _generate_code(self, length: int = 10) -> str:
        """
        生成一个唯一的兑换码。

        使用 UUID 生成唯一标识符，然后将其转换为大写字母和数字组成的字符串。

        :param length: 所需的兑换码长度
        :return: 唯一的兑换码字符串
        """
        try:
            for _ in range(10):
                # 生成 UUID 并转换为字符串
                unique_id = str(uuid.uuid4())

                # 移除连字符并转换为大写
                code = unique_id.replace("-", "").upper()

                # 调整字符串长度
                if len(code) > length:
                    code = code[:length]
                elif len(code) < length:
                    code = code.ljust(length, "A")  # 使用 'A' 填充到所需长度
                # 确保唯一
                if not await self.is_code_exists(code):
                    return code
        except Exception as err:
            logger.error(f"An error occurred: {err}", exc_info=True)
            print(f"an error occurred,{traceback.format_exc()}")

    def create_table(self):
        """
        创建redemption code表
            索引: id
                  code
        """
        try:
            with mysql.connector.connect(**self.DB_CONFIG) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS redemption_codes (
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            code VARCHAR(255) UNIQUE NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            user_id BIGINT,
                            used_at TIMESTAMP NULL,
                            vip_days INT DEFAULT 0,
                            vip_points INT DEFAULT 0,
                            permanent_point_balance INT DEFAULT 0,
                            is_active BOOLEAN DEFAULT 1,
                            caption TEXT
                        );
                        """
                    )
                conn.commit()
        except Exception as err:
            logger.error(f"an error occurred: {err}", exc_info=True)
            print(f"an error orrurred{traceback.format_exc()}")

    async def _insert_code(
        self,
        code,
        user_id=None,
        used_at=None,
        vip_days=0,
        vip_points=0,
        permanent_point_balance=0,
        is_active=True,
        caption=None,
    ):
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO redemption_codes (code, user_id, used_at, vip_days, vip_points, permanent_point_balance, is_active, caption)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            code,
                            user_id,
                            used_at,
                            vip_days,
                            vip_points,
                            permanent_point_balance,
                            is_active,
                            caption,
                        ),
                    )
                    await conn.commit()
        except Exception as err:
            logger.error(f"插入code{code}时出现一个错误, {err}", exc_info=True)
            print(
                f"an error occurred when insert an code: {code}, {traceback.format_exc()}"
            )

    async def is_code_exists(self, code: str) -> bool:
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT code FROM redemption_codes WHERE code = %s", (code,)
                    )
                    row = await cursor.fetchone()
                    return row is not None
        except Exception as err:
            logger.error(
                f"search is code exists:{code}时出现一个错误, {err}", exc_info=True
            )
            print(
                f"an error occurred when search an code: {code}, {traceback.format_exc()}"
            )

    async def add_redemption_code(
        self,
        vip_days: int,
        vip_points: int,
        permanent_point_balance: int,
        is_active: bool = True,
        caption: str = "",
    ) -> str:
        try:
            code = await self._generate_code()
            while await self.is_code_exists(code):
                code = await self._generate_code()
            await self._insert_code(
                code=code,
                vip_days=vip_days,
                vip_points=vip_points,
                permanent_point_balance=permanent_point_balance,
                is_active=is_active,
                caption=caption,
            )
            return code
        except Exception as err:
            logger.error(
                f"there is an error then add a code: {code}, {err}", exc_info=True
            )
            print(
                f"an error occurred when add an code: {code}, {traceback.format_exc()}"
            )

    async def delete_code(self, code: str) -> dict:
        """
        从数据库中删除指定的兑换码。

        :param code: 要删除的兑换码
        :return: {"success": bool, "message": str}

        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "DELETE FROM redemption_codes WHERE code = %s", (code,)
                    )
                    await conn.commit()
                    if cursor.rowcount > 0:
                        return {
                            "success": True,
                            "message": f"Code {code} has been deleted successfully",
                        }
                    else:
                        return {"success": False, "message": f"Code {code} not found"}
        except Exception as err:
            logger.error(
                f"An error occurred when try to delete a code: {code}, {err}",
                exc_info=True,
            )
            print(
                f"an error occurred when delete an code: {code}, {traceback.format_exc()}"
            )
            return {"success": False, "message": f"Error deleting code: {str(err)}"}

    async def add_many_redemption_code(
        self,
        number: int,
        vip_days: int,
        vip_points: int,
        permanent_point_balance: int,
        is_active: bool = True,
        code_length: int = 10,
        caption: str = "",
    ) -> dict:
        """
        批量生成并添加兑换码。
        :param number: 要生成的兑换码数量
        :param vip_days: VIP天数
        :param vip_points: VIP点数
        :param permanent_point_balance: 永久点数余额
        :param is_active: 是否激活
        :param code_length: 兑换码长度
        :param caption: 备注
        :return: 包含生成信息和兑换码列表的字典 codes = rsp["code_list"]
        """
        try:
            codes = []
            # 生成指定数量的唯一兑换码
            while len(codes) < int(number):
                new_code = await self._generate_code(code_length)
                if new_code not in codes:  # 确保在本批次中唯一
                    codes.append(new_code)

            # 批量插入数据库
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.executemany(
                        """
                        INSERT INTO redemption_codes 
                        (code, vip_days, vip_points, permanent_point_balance, is_active, caption)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        [
                            (
                                code,
                                vip_days,
                                vip_points,
                                permanent_point_balance,
                                is_active,
                                caption,
                            )
                            for code in codes
                        ],
                    )
                    await conn.commit()
            return {
                "number": number,
                "vip_days": vip_days,
                "vip_points": vip_points,
                "permanent_point_balance": permanent_point_balance,
                "code_list": codes,
            }
        except Exception as err:
            logger.error(
                f"An error occurred when try to add many codes, {err}", exc_info=True
            )
            print(
                f"an error occurred when try to add many codes: {traceback.format_exc()}"
            )

    async def get_redemption_code_info(self, code: str) -> RedemptionCodesInfo | None:
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        SELECT id,
                            code,
                            UNIX_TIMESTAMP(created_at) AS created_at,
                            UNIX_TIMESTAMP(updated_at) AS updated_at,
                            user_id,
                            UNIX_TIMESTAMP(used_at) AS used_at,
                            vip_days,
                            vip_points,
                            permanent_point_balance,
                            is_active,
                            caption
                        FROM redemption_codes WHERE code = %s;
                        """,
                        (code,),
                    )
                    row = await cursor.fetchone()
            if row is None:
                return None
            else:
                return RedemptionCodesInfo.from_list(row)
        except Exception as err:
            logger.error(
                f"An error occurred when try to get code info, {err}", exc_info=True
            )
            print(
                f"an error occurred when get the info of the code: {code}, {traceback.format_exc()}"
            )

    async def use_redemption_code(self, code: str, user_id: int) -> bool:
        """
        使用兑换码
        parm: code: int
        parm: user_id: int -> user_id
        return  bool -> update the redemption succeed?
        """
        try:
            info = await self.get_redemption_code_info(code)
            if info is None or info.is_active == 0:
                return False
            if info.used_at is not None and time.time() - info.used_at < 10:
                return False
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """
                        UPDATE redemption_codes
                        SET user_id = %s, used_at = CURRENT_TIMESTAMP, is_active = 0
                        WHERE code = %s
                        """,
                        (user_id, code),
                    )
                    await conn.commit()
                    return cursor.rowcount > 0
        except Exception as err:
            logger.error(
                f"An error occurred when try to update the codes, {err}", exc_info=True
            )
            print(
                f"an error occurred when try to update the codes: {traceback.format_exc()}"
            )