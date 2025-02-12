import asyncio
from src.core.database.service.chatsService import ChatService
from src.core.database.service.vip_service import vipService
from src.core.tools.task_keeper import TaskKeeper
from telegram import Update
from telegram.ext import ContextTypes

class InfoSaver:
    _instance = None
    vip_service = vipService()
    chats = ChatService()
    task_keeper = TaskKeeper()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def _store_user_info(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        store user info
        """
        # 后台保存用户信息
        add_user_task = asyncio.create_task(
            cls.vip_service.add_user(
                user_id=update.message.from_user.id,
                chat_id=update.message.chat.id,
                user_name=update.message.from_user.username,
                display_name=" ".join(
                    filter(
                        None,
                        [
                            update.message.from_user.first_name,
                            update.message.from_user.last_name,
                        ],
                    )
                ),
            )
        )
        cls.task_keeper.add_task(add_user_task)

    @classmethod
    async def _store_chat_info(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        store chat info
        """
        # 如果是message类型
        if update.message and update.message.chat.id:
            add_chat_task = asyncio.create_task(
                cls.chats.add_chat(
                    chat_id=update.message.chat.id,
                    chat_type=update.message.chat.type,
                    title=update.message.chat.title,
                )
            )
            cls.task_keeper.add_task(add_chat_task)
            
    @classmethod
    async def info_save(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await cls._store_chat_info(update, context)
        await cls._store_user_info(update, context)