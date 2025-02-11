from core.database.db.messageHistory import ChatMessageHistory
import copy
import traceback
# from telegram import Update
# Update.message.from_user.is_bot
from src.core.logger import logger
from telegram import Message


class MessageHistoryService:
    def __init__(self):
        self.msgHistory = ChatMessageHistory()

    # get message history
    async def get_message_history(self, message: Message, limit=10, allow_photo=True):
        """
        获取消息的历史记录
        parm: message:Message
        parm: limit: int
        return history: dict
        """
        chat_id = message.chat.id
        current_message_id = message.message_id
        history = await self.msgHistory._get_chat_history(
            chat_id=chat_id,
            current_message_id=current_message_id,
            limit=limit,
            allow_photo=allow_photo,
        )
        return history

    async def get_message_history_by_id(
        self, chat_id, current_message_id, limit=10, allow_photo=True
    ):
        """
        通过chat_id和message_id获取message_history
        """
        history = await self.msgHistory._get_chat_history(
            chat_id=chat_id,
            current_message_id=current_message_id,
            limit=limit,
            allow_photo=allow_photo,
        )
        return history

    def has_url_in_history(self, message_history):
        """
        检查消息历史记录中是否包含URL（图片）。

        :param message_history: 消息历史记录列表
        :return: 布尔值，如果包含URL则返回True，否则返回False
        """
        for message in message_history:
            content = message.get("content", [])
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "image_url":
                        return True
            elif isinstance(content, str):
                # 如果content是字符串，我们假设它不包含URL
                continue
        return False

    def prepend_user_msg_to_history(self, message_text, photo_url=None, history=[]):
        """
        将当前用户的消息添加到已获取的历史记录开头。

        :param message_text: 用户的文本消息
        :param photo_url: 可选，用户发送的图片URL
        :param history: 已获取的聊天历史记录列表
        :return: 更新后的历史记录列表
        """
        history = copy.deepcopy(history)
        content = []

        # 添加文本消息
        if message_text:
            content.append({"type": "text", "text": message_text})

        # 添加图片URL（如果有）
        if photo_url:
            content.append({"type": "image_url", "image_url": {"url": photo_url}})

        if content:
            # 创建新的消息对象
            new_message = {"role": "user", "content": content}

            # 将新消息添加到历史记录开头
            history.insert(0, new_message)

        return self.merge_consecutive_messages(history)

    def prepend_msgs_to_history(self, messages=[], history=[]):
        """
        将当前用户的消息添加到已获取的历史记录开头。

        :param prompt_msg: 用户的文本消息
        :param photo_url: 可选，用户发送的图片URL
        :param history: 已获取的聊天历史记录列表
        :return: 更新后的历史记录列表
        messages应当是一个列表[]
        {
            "role": "user" | "system" | "assistant",
            "content": []
        }
        {
            "type": "text" | "image_url",
            "text": text OR
            "image_url": {
                    "url": photo_url
                }
        }
        """
        history = copy.deepcopy(history)
        history = (messages + history) if messages else history
        return self.merge_consecutive_messages(history)

    def append_msg_to_history(self, message_text, photo_url=None, history=[]):
        """
        将当前用户的消息追加到已获取的历史记录末尾。

        :param message_text: 用户的文本消息
        :param photo_url: 可选，用户发送的图片URL
        :param history: 已获取的聊天历史记录列表
        :return: 更新后的历史记录列表
        """
        history = copy.deepcopy(history)
        content = []

        # 添加文本消息
        if message_text:
            content.append({"type": "text", "text": message_text})

        # 添加图片URL（如果有）
        if photo_url:
            content.append({"type": "image_url", "image_url": {"url": photo_url}})

        # 创建新的消息对象
        new_message = {"role": "user", "content": content}

        # 将新消息追加到历史记录末尾
        history.append(new_message)

        return self.merge_consecutive_messages(history)

    def _process_assistant_images(self, message):
        """
        处理 assistant 消息中的图片，将其分离为文本和图片消息。

        :param message: 单个消息字典
        :return: 处理后的消息列表
        """
        text_content = []
        image_content = []
        for item in message["content"]:
            if item["type"] == "image_url":
                image_content.append(item)
            else:
                text_content.append(item)

        processed = []
        if text_content:
            processed.append({"role": "assistant", "content": text_content})
        if image_content:
            processed.append({"role": "user", "content": image_content})
        return processed if processed else [message]

    def _merge_same_role_messages(self, processed_history):
        """
        合并连续的相同角色消息。

        :param processed_history: 经过图片处理的消息历史
        :return: 合并后的消息历史
        """
        merged_history = []
        current_role = None
        current_message = None

        for message in processed_history:
            role = message["role"]
            content = message["content"]

            if role == current_role:
                for content_item in content:
                    if (
                        content_item["type"] == "text"
                        and current_message["content"][-1]["type"] == "text"
                    ):
                        current_message["content"][-1]["text"] += (
                            " " + content_item["text"]
                        )
                    else:
                        current_message["content"].append(content_item)
            else:
                if current_message:
                    merged_history.append(current_message)
                current_role = role
                current_message = {"role": role, "content": content}

        if current_message:
            merged_history.append(current_message)

        return merged_history

    def merge_consecutive_messages(self, history):
        """
        处理历史记录中的消息，将 assistant 角色中的图片消息转换为 user 角色，
        然后合并连续的相同角色消息。

        :param history: 原始的聊天历史记录列表
        :return: 处理后的聊天历史记录列表
        """
        history = copy.deepcopy(history)
        try:
            if not history:
                return history

            # 第一步：处理 assistant 消息中的图片
            processed_history = []
            for message in history:
                if message["role"] == "assistant":
                    processed_history.extend(self._process_assistant_images(message))
                else:
                    processed_history.append(message)

            # 第二步：合并连续的相同角色消息
            merged_history = self._merge_same_role_messages(processed_history)

            # 确保不以assistant开头
            if merged_history[0]["role"] == "assistant":
                # 创建一个空的 user 消息
                merged_history = self.prepend_msgs_to_history(
                    ".", history=merged_history
                )
            return merged_history

        except Exception:
            logger.error(f"处理消息时出现错误, 原始消息: {history}", exc_info=True)
            print(f"处理消息时出现错误, 原始消息: {history}, {traceback.format_exc()}")
            return history  # 如果出错，返回原始历史记录

    async def _store_message(
        self,
        chat_id,
        message_id,
        user_id,
        from_type,
        message_text,
        photo_url_list: list,
        reply_to_message_id=None,
    ):
        """
        储存信息
        parm: photo_url_list: list, None兼容为 -> []
        return: None
        """
        await self.msgHistory._store_message(
            chat_id,
            message_id,
            user_id,
            from_type,
            message_text,
            photo_url_list=photo_url_list,
            reply_to_message_id=reply_to_message_id,
        )

    async def store_message(self, message: Message, photo_url_list: list = None):
        """
        储存message
        return None
        """
        chat_id = message.chat.id
        message_id = message.message_id
        from_type = "bot" if message.from_user.is_bot else "user"
        user_id = message.from_user.id if from_type == "user" else None
        message_text = message.text or message.caption or ""
        reply_to_message_id = (
            message.reply_to_message.message_id if message.reply_to_message else None
        )
        await self._store_message(
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            photo_url_list=photo_url_list,
            from_type=from_type,
            message_text=message_text,
            reply_to_message_id=reply_to_message_id,
        )

    async def delete_message(self, chat_id, message_id):
        """
        删除信息
        return: None
        """
        await self.msgHistory.delete_message(chat_id=chat_id, message_id=message_id)
