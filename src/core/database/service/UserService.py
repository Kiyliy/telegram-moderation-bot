import time
from src.core.config.config import config
from src.core.database.db.UserDatabase import UserDatabase


class UserService:
    def __init__(self) -> None:
        self.user_db = UserDatabase()
        self.config = config

    async def add_user(
        self, user_id: int, user_name: str, display_name: str, chat_id: int
    ) -> dict:
        """
        添加用户, 包括user_id, user_name, display_name, permanent_point_balance 字段，其余都为默认值

        :param user_id: 用户ID
        :param user_name: 用户名
        :param display_name: 显示名
        :return: {"success": bool, "message": str}
        """
        # 1. 检查用户是否存在, 如果存在, 检查是否需要更新name
        user_info = await self.user_db.get_user_info(user_id=user_id)
        if user_info:
            # # 2.1 如果用户存在, 检查是否需要更新name
            # if (
            #     user_info.user_name != user_name
            #     or user_info.display_name != display_name
            # ):
            #     return await self.user_db.update_user_disply_info(
            #         user_id=user_id, user_name=user_name, display_name=display_name
            #     )
            # else:
            #     return {"success": True, "message": "User already exists"}
            return
        # 2. 用户不存在, 添加用户
        rsp = await self.user_db.add_user(
            user_id=user_id,
            user_name=user_name,
            display_name=display_name,
            chat_id=chat_id,
        )
        return rsp

    async def get_user_language(self, user_id: int) -> str | None:
        '''
        获取用户的语言设置
        '''
        user_lang = await self.user_db.get_user_language(user_id=user_id)
        return user_lang

    async def update_has_used_ai_true(self, user_id) -> dict:
        """
        更新用户是否使用过AI
        :param user_id: 要查询的用户ID
        :return: {"success": bool, "message": str}
        """
        user_info = await self.get_user_info(user_id=user_id)
        if user_info:
            if user_info.has_used_ai:
                return {"success": True, "message": "User already used AI"}
            else:
                rsp = await self.user_db.update_user_ai_status(
                    user_id=user_id, has_used_ai=True
                )
                return rsp
        else:
            return {"success": False, "message": "User not found"}

    async def daily_checkin(self, user_id) -> dict:
        """
        每日签到
        parm: user_id
        return {"success": bool, "message": str,"reset": bool}
        """
        daily_checkin_amount = self.config.get_daily_points()
        rsp = await self.user_db.reset_daily_balance(
            user_id=user_id, amount=daily_checkin_amount
        )
        return rsp

    async def _add_vip(
        self, user_id: int, vip_points: int, vip_days: int, permanent_point_balance: int
    ) -> dict:
        """
        Recharge a user's VIP points and days, and update their permanent point balance.

        :param user_id: The ID of the user
        :param vip_points: The VIP points to add
        :param vip_days: The VIP days to add
        :param permanent_point_balance: The permanent points to add
        :return: {"success": bool, "message": str}
        """
        try:
            user_info = await self.user_db.get_user_info(user_id=user_id)
            daily_point_last_reset_at = user_info.daily_point_last_reset_at
            current_timestamp = int(time.time())

            # Check if VIP time has expired
            if user_info.vip_point_expired_date < current_timestamp:
                user_info.vip_point_balance = 0
                user_info.vip_point_expired_date = current_timestamp

            # Update user info with new VIP points and days, and permanent point balance
            new_vip_point_balance = user_info.vip_point_balance + vip_points
            new_vip_point_expired_date = (
                user_info.vip_point_expired_date + vip_days * 86400
            )  # 86400 seconds in a day
            new_permanent_point_balance = (
                user_info.permanent_point_balance + permanent_point_balance
            )

            rsp = await self.user_db._update_user_info(
                user_id=user_info.user_id,
                user_name=user_info.user_name,
                display_name=user_info.display_name,
                is_blocked=user_info.is_blocked,
                daily_point_balance=user_info.daily_point_balance,
                daily_point_last_reset_at=daily_point_last_reset_at,
                vip_point_balance=new_vip_point_balance,
                vip_point_expired_date=new_vip_point_expired_date,
                permanent_point_balance=new_permanent_point_balance,
                chat_id=user_info.chat_id,
            )

            if rsp["success"]:
                return {"success": True, "message": "Recharge successful"}
            else:
                return {"success": False, "message": rsp["message"]}

        except Exception as err:
            return {"success": False, "message": f"Unexpected error: {str(err)}"}

    async def use_balance(self, user_id: int, cost: int) -> dict:
        """
        Deduct balance from the user in the order of daily balance, VIP balance, and permanent balance.

        :param user_id: The ID of the user
        :param cost: The cost to deduct from the user's balance
        :return: {
            "success": bool, 是否未发生异常
            "balance_enough": bool, 用户余额是否足够
            "daily":int, 使用的daily积分
            "vip": int, 使用的vip积分
            "permanent": int, 使用的永久积分
            }
        >>> 确保success和balance_enough为True即为调用成功
        """
        # 0. 如果cost为0, 直接返回
        if cost == 0:
            return {
                "success": True,
                "balance_enough": True,
                "daily": 0,
                "vip": 0,
                "permanent": 0,
            }
        try:
            # 1. 获取用户信息, 检查用户是否存在
            user_info = await self.user_db.get_user_info(user_id=user_id)

            if not user_info:
                return {
                    "success": True,
                    "balance_enough": False,
                    "daily": 0,
                    "vip": 0,
                    "permanent": 0,
                }

            # 2. 检查用户信息, 是否自动签到或者会员到期
            current_timestamp = int(time.time())

            # 2.1 如果需要重新签到, 签到后重新获取信息
            last_reset_time = user_info.daily_point_last_reset_at
            if current_timestamp - last_reset_time >= 18 * 3600:
                await self.daily_checkin(user_info.user_id)
                user_info = await self.user_db.get_user_info(user_id=user_id)

            # 2.2 检查会员是否到期
            if user_info.vip_point_expired_date < current_timestamp:
                user_info.vip_point_balance = 0

            # 2.3 获取用户积分
            daily_balance = user_info.daily_point_balance
            vip_balance = user_info.vip_point_balance
            permanent_balance = user_info.permanent_point_balance

            # 3. 计算每日积分, vip积分, 永久积分的使用量
            daily_balance_change = 0
            vip_balance_change = 0
            permanent_balance_change = 0
            if daily_balance >= cost:
                daily_balance_change = cost
            elif daily_balance + vip_balance >= cost:
                daily_balance_change = daily_balance
                vip_balance_change = cost - daily_balance
            elif daily_balance + vip_balance + permanent_balance >= cost:
                daily_balance_change = daily_balance
                vip_balance_change = vip_balance
                permanent_balance_change = cost - daily_balance - vip_balance
            # 如果积分不足, 则返回
            else:
                return {
                    "success": False,
                    "balance_enough": False,
                    "daily": 0,
                    "vip": 0,
                    "permanent": 0,
                }

            # 4. 更新用户积分
            await self.user_db.set_banlance(
                user_id=user_id,
                daily_points=daily_balance - daily_balance_change,
                vip_points=vip_balance - vip_balance_change,
                vip_expired_date=time.time(),
                permanent_points=permanent_balance - permanent_balance_change,
            )

            return {
                "success": True,
                "balance_enough": True,
                "daily": daily_balance_change,
                "vip": vip_balance_change,
                "permanent": permanent_balance_change,
            }

        except Exception:
            return {
                "success": False,
                "balance_enough": False,
                "daily": 0,
                "vip": 0,
                "permanent": 0,
            }

    async def check_balance(self, user_id: int) -> dict:
        """
        Check the balance of a user, including daily, VIP, and permanent balances.

        :param user_id: The ID of the user
        :return: int, 用户当前剩余的积分
        if user_id not found, return 0
        """
        try:
            user_info = await self.user_db.get_user_info(user_id=user_id)

            if not user_info:
                return 0

            current_timestamp = int(time.time())

            # 如果需要重新签到, 签到后重新获取信息
            last_reset_time = user_info.daily_point_last_reset_at
            if current_timestamp - last_reset_time >= 18 * 3600:
                await self.daily_checkin(user_info.user_id)
                user_info = await self.user_db.get_user_info(user_id=user_id)

            # 如果会员到期, vip积分视为0
            vip_balance = user_info.vip_point_balance
            if user_info.vip_point_expired_date < current_timestamp:
                vip_balance = 0

            return (
                user_info.daily_point_balance
                + vip_balance
                + user_info.permanent_point_balance
            )

        except Exception:
            return 0
