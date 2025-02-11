# 首先导入初始化模块，这会触发所有handler的注册
import initial

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    CommandHandler,
)
import os
from telegram import BotCommand
# from src.core.service.logger import logger
import asyncio
from textwrap import dedent
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageRegistry import MessageRegistry
import time
import initial


async def run_bot(application: Application):
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await asyncio.Future()

async def main():
    # 加载环境变量
    load_dotenv()

    # 获取bot token
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("Bot token not found in environment variables")

    # 初始化处理器
    # message_handler = MessageHandler()
    callback_registry = CallbackRegistry()

    # 创建Telegram应用
    proxy = os.getenv("PROXY")
    if proxy:
        # logger.info(f"Using proxy: {proxy}")
        application = (
            Application.builder()
            .token(bot_token)
            .proxy(proxy)
            .get_updates_proxy(proxy)
            .build()
        )
    else:
        application = Application.builder().token(bot_token).build()


    # 添加消息处理器（处理图片和视频）
    application.add_handler(
        MessageHandler(
            filters.ALL,
            # filters.PHOTO | filters.VIDEO,
            MessageRegistry.dispatch
        ),
        group=1
    )

    # 添加回调查询处理器
    application.add_handler(
        CallbackQueryHandler(callback_registry.dispatch)
    )

    # 设置机器人命令
    await application.bot.set_my_commands([
        BotCommand("help", "显示帮助信息"),
        BotCommand("appeal", "申诉被删除的消息"),
        BotCommand("settings", "审核设置 (仅管理员)"),
        BotCommand("stats", "查看统计信息 (仅管理员)"),
        BotCommand("logs", "查看审核日志 (仅管理员)")
    ])

    try:
        # logger.info("Bot is starting...")
        print("Bot is starting...")
        await run_bot(application)
    except Exception as e:
        # logger.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")
    finally:
        await application.stop()
        # logger.info("Bot stopped")
        print("Bot stopped")


if __name__ == "__main__":
    print(dedent(
        f"""
        #######################################################
                    Telegram Moderation Bot
                    启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
                    DEBUG模式: {os.getenv("DEBUG", "False")}
        #######################################################
        """
    ).strip())
    
    asyncio.run(main())
