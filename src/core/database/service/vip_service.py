from core.database.db.user_redempton_codes import userRedemptionCodes
from src.core.logger import logger
import traceback
from src.core.database.service.UserService import UserService
from src.core.database.service.RedemptionService import RedemptionCodeService


class vipService(UserService, userRedemptionCodes, RedemptionCodeService):
    """
    VIP服务类，继承自userRedemptionCodes
    必须是UserService在前，userRedemptionCodes在后
    """

    def __init__(self) -> None:
        """
        初始化父类方法
        """
        UserService.__init__(self)
        userRedemptionCodes.__init__(self)
        RedemptionCodeService.__init__(self)

    async def useRedemptionCode(self, code: str, user_id: int) -> dict:
        """
        使用兑换码

        :param code: 兑换码
        :param user_id: 用户ID
        :return: dict {"success": bool, "message": str}
        """
        try:
            # 调用父类的方法来处理兑换码使用
            result = await self.user_use_redemptionCode(user_id, code)

            if result["success"]:
                return {"success": True, "message": "兑换码使用成功，VIP权益已更新"}
            else:
                error_message = (
                    f"兑换失败: {result['message']},{traceback.format_exc()}"
                )
                logger.error(
                    f"User {user_id} failed to use redemption code {code}: {error_message}"
                )
                print(f"Error: {error_message}")  # 控制台打印错误信息
                return {"success": False, "message": error_message}

        except Exception as e:
            error_message = (
                f"处理兑换码时发生未知错误: {str(e)}{traceback.format_exc()}"
            )
            logger.error(
                f"Unexpected error for user {user_id} using code {code}: {error_message}"
            )
            logger.error(traceback.format_exc())  # 记录完整的堆栈跟踪
            print(f"Error: {error_message}")  # 控制台打印错误信息
            print(traceback.format_exc())  # 控制台打印堆栈跟踪
            return {"success": False, "message": error_message}


# 使用示例
async def example_usage():
    vip_service = vipService()
    result = await vip_service.useRedemptionCode("SOMECODE123", 12345)
    if result["success"]:
        print(f"Success: {result['message']}")
    else:
        print(f"Failed: {result['message']}")


# 在异步环境中运行示例
# import asyncio
# asyncio.run(example_usage())
