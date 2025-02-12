from src.core.database.db.RedemptionCodesDatabase import (
    RedemptionCodesDatabase,
    RedemptionCodesInfo,
)


class RedemptionCodeService:
    def __init__(self):
        self.code_service = RedemptionCodesDatabase()

    async def add_redemption_code(
        self, vip_days, vip_points, permanent_point_balance, caption
    ):
        """
        生成一个兑换码
        parm: vip_days: int
        parm: vip_points: int
        parm: permanent_point_balance: int
        parm: caption: str
        return: code
        """
        code: RedemptionCodesInfo = await self.code_service.add_redemption_code(
            vip_days=vip_days,
            vip_points=vip_points,
            permanent_point_balance=permanent_point_balance,
            is_active=True,
            caption=caption,
        )
        return code

    async def delete_code(self, code):
        rsp = await self.code_service.delete_code(code)
        return rsp

    async def add_many_redemption_code(
        self,
        number: int,
        vip_days: int,
        vip_points: int,
        permanent_point_balance: int,
        code_length: int = 32,
        is_active: bool = True,
        caption: str = "",
    ):
        """
        批量生成并添加兑换码。
        :param number: 要生成的兑换码数量
        :param vip_days: VIP天数
        :param vip_points: VIP点数
        :param permanent_point_balance: 永久点数余额
        :param is_active: 是否激活
        :param code_length: 兑换码长度
        :param caption: 备注
        :return: 包含生成信息和兑换码列表的字典 response["code_list"]
        """
        rsp = await self.code_service.add_many_redemption_code(
            number=int(number),
            vip_days=int(vip_days),
            vip_points=int(vip_points),
            permanent_point_balance=int(permanent_point_balance),
            is_active=is_active,
            code_length=code_length,
            caption=caption,
        )
        return rsp

    async def _use_redemption_code(self, code, user_id):
        """
        使用兑换码
        parm: code: int
        parm: user_id: int -> user_id
        return bool
        """
        rsp = await self.code_service.use_redemption_code(code=code, user_id=user_id)
        return rsp

    async def get_redemption_code_info(self, code):
        info = await self.code_service.get_redemption_code_info(code=code)
        return info
