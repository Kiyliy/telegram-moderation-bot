from typing import Dict, Any, Optional, List
import traceback
from src.core.logger import logger
from src.core.database.db.ChatDatabase import ChatDatabase, ChatInfo
import json


class ChatService:
    def __init__(self, db: ChatDatabase = None):
        """
        初始化ChatService

        :param db: ChatDatabase实例，如果为None则创建新实例
        """
        self.db = ChatDatabase() if db is None else db

    async def add_chat(
        self, chat_id: int, chat_type: str, title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        添加新的chat或者更新chat

        :param chat_id: Telegram的chat_id
        :param chat_type: 聊天类型，必须是ChatType枚举中的值
        :param title: 群组或频道的标题（对于私聊可以为None）
        :return: 包含操作结果的字典 {"success": bool, "message": str}
        """
        try:
            # 1. 检查chat是否存在
            chat_info: ChatInfo | None = await self.db.get_chat_info(chat_id=chat_id)

            # 2. 如果chat存在, 判断是否一致, 如果一致, 则返回
            if chat_info:
                # 2.1 一致, 无需更新
                if chat_info.chat_type == chat_type and chat_info.title == title:
                    return {
                        "success": True,
                        "message": "Chat already exists and is up to date",
                        "operation": "update_chat_skip",
                    }
                # 2.2 不一致, 更新信息
                else:
                    result = await self.db.update_chat_info(
                        chat_id=chat_id, chat_type=chat_type, title=title
                    )
                    if result["success"]:
                        return {
                            "success": True,
                            "message": "Chat updated successfully",
                            "operation": "update_chat_success",
                        }
            # 2.3 不存在, 插入数据
            else:
                result = await self.db.add_chat(
                    chat_id=chat_id, chat_type=chat_type, title=title
                )
                if result["success"]:
                    return {
                        "success": True,
                        "message": "Chat added successfully",
                        "operation": "add_chat_success",
                    }

            # 3. 添加失败
            return {
                "success": False,
                "message": "Failed to add chat",
                "operation": "add_chat_error",
            }
        except Exception as e:
            logger.error(f"添加聊天记录时出错: {str(e)}", exc_info=True)
            print(f"添加聊天记录时出错: {traceback.format_exc()}")
            return {"success": False, "message": f"添加聊天记录时出错: {str(e)}"}

    async def update_chat(
        self,
        chat_id: int,
        chat_type: Optional[str] = None,
        title: Optional[str] = None,
        owner_id: Optional[int] = None,
        ads: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        更新指定的聊天记录

        :param chat_id: 要更新的聊天的chat_id
        :param chat_type: 聊天类型，必须是ChatType枚举中的值
        :param title: 群组或频道的标题
        :param owner_id: 群主或渠道商的user_id
        :return: 包含操作结果的字典 {"success": bool, "message": str}
        """
        try:
            result = await self.db.update_chat_info(chat_id, chat_type, title)
            return {"success": result["success"], "message": result["message"]}
        except Exception as e:
            logger.error(f"更新聊天记录时出错: {str(e)}", exc_info=True)
            print(f"更新聊天记录时出错: {traceback.format_exc()}")
            return {"success": False, "message": f"更新聊天记录时出错: {str(e)}"}

    async def update_chat_ads(self, chat_id: int, ads: str) -> Dict[str, Any]:
        try:
            result = await self.db.update_chat_ads(chat_id, ads)
            return {"success": result["success"], "message": result["message"]}
        except Exception as e:
            logger.error(f"更新聊天广告时出错: {str(e)}", exc_info=True)
            print(f"更新聊天广告时出错: {traceback.format_exc()}")
            return {"success": False, "message": f"更新聊天广告时出错: {str(e)}"}

    async def bind_group_to_user(self, group_id, user_id):
        '''
        将群组绑定用户 -> 意思是这个群组是这个用户的
        '''
        try:
            result = await self.db.bind_group_to_user(group_id, user_id)
            return result
        except Exception as e:
            logger.error(f"绑定群组到用户时出错: {str(e)}", exc_info=True)
            print(f"绑定群组到用户时出错: {traceback.format_exc()}")
            return {"success": False, "message": f"绑定群组到用户时出错: {str(e)}"}

    async def unbind_group_from_user(self, group_id, user_id):
        '''
        解绑群组
        '''
        try:
            result = await self.db.unbind_group_from_user(group_id, user_id)
            return result
        except Exception as e:
            logger.error(f"解绑群组时出错: {str(e)}", exc_info=True)
            print(f"解绑群组时出错: {traceback.format_exc()}")
            return {"success": False, "message": f"解绑群组时出错: {str(e)}"}

    async def get_owner_groups(self, user_id: int) -> List[Dict[str, Any]]:
        '''
        获取用户所有的群组
        '''
        try:
            groups = await self.db.get_owner_groups(user_id)
            return groups
        except Exception as e:
            logger.error(f"获取用户所有的群组时出错: {str(e)}", exc_info=True)
            print(f"获取用户所有的群组时出错: {traceback.format_exc()}")
            return []



    async def get_chat_info(self, chat_id: int) -> Optional[ChatInfo]:
        """
        获取指定聊天的信息

        :param chat_id: 要查询的聊天的chat_id
        :return: 包含聊天信息的字典，如果不存在则返回None
        字典为一个ChatInfo对象
        """
        try:
            chat_info: ChatInfo = await self.db.get_chat_info(chat_id)
            return chat_info
        except Exception as e:
            logger.error(f"获取聊天信息时出错: {str(e)}", exc_info=True)
            print(f"获取聊天信息时出错: {traceback.format_exc()}")
            return None

    async def _get_chats_ads(self, chat_id: int) -> Optional[dict]:
        """
        获取chat_info的ads字段
        :param chat_id: 要查询的聊天的chat_id
        :return: 一段json, 包含广告链接和可能的button, 获取失败返回None
        """
        try:
            chat_info: ChatInfo = await self.get_chat_info(chat_id)
            if chat_info.ads:
                return json.loads(chat_info.ads)
            return {}
        except Exception as e:
            logger.error(f"获取chat_info的ads字段时出错: {str(e)}", exc_info=True)
            print(f"获取chat_info的ads字段时出错: {traceback.format_exc()}")
            # 返回None, 表示获取失败
            return None

    async def get_chats_by_owner(self, owner_id: int) -> List[Dict[str, Any]]:
        """
        获取指定所有者的所有聊天

        :param owner_id: 所有者的user_id
        :return: 包含所有聊天信息的列表，每个元素是一个字典
        """
        try:
            chats = await self.db.get_chats_by_owner(owner_id)
            return chats
        except Exception as e:
            logger.error(f"获取所有者聊天列表时出错: {str(e)}", exc_info=True)
            print(f"获取所有者聊天列表时出错: {traceback.format_exc()}")
            return []
