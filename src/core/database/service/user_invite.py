# 用户邀请模块, 用于处理用户邀请和奖励

from core.database.db.UserDatabase import UserDatabase
from src.core.database.service.delayLogService import FullyMatchedDelayedLoggingSystem
import time

class UserInviteError:
    SELF_INVITE = 'User cannot invite himself'
    ALREADY_INVITED = 'User already invited'
    TIME_LIMIT = 'User registration time exceeds 24 hours'

class UserInviteService:
    def __init__(self):
        self.user_database = UserDatabase()
        self.delay_log_service = FullyMatchedDelayedLoggingSystem()

    async def invite_user(self, user_id: int, invited_by_user_id: int, user_lang: str) -> dict:
        # # 被邀请人存在, 说明已经被邀请过了
        # user_info = await self.user_database.get_user_info(user_id)
        # if user_info is not None:
        #     return {"status": False, "user_info": user_info}

        # 被邀请人会自动注册, 所以需要检测被邀请人是否已经被邀请了 + 注册时间是否在24小时内
        user_info = await self.user_database.get_user_info(user_id)
        if user_id == invited_by_user_id:
            return {
                "status": False,
                "user_info": user_info,
                "errmsg": UserInviteError.SELF_INVITE,
            }
        if user_info.invited_by_user_id is not None:
            return {
                "status": False,
                "user_info": user_info,
                "errmsg": UserInviteError.ALREADY_INVITED,
            }
        if user_info.create_at < time.time() - 24 * 60 * 60:
            return {
                "status": False,
                "user_info": user_info,
                "errmsg": UserInviteError.TIME_LIMIT,
            }

        # 被邀请人不存在, 则添加被邀请人, 邀请成功
        await self.user_database.add_invited_by_user_id(user_id, invited_by_user_id)
        return {"status": True, "user_info": user_info}
