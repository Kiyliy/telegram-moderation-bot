
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.base_handler import BaseHandler
from telegram import Update
from telegram.ext import ContextTypes


# 使用示例
class MessageHandler(BaseHandler):
    def __init__(self):
        super().__init__()

    @MessageRegistry.register(MessageFilters.match_regex(r"^/start(?:\s+(?P<param>\w+))?$"))
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, param: str = None):
        if param:
            await update.message.reply_text(f"Started with parameter: {param}")
        else:
            await update.message.reply_text("Started without parameter")

    @MessageRegistry.register(MessageFilters.match_regex(r"^help"))
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("This is help message")

    @MessageRegistry.register(MessageFilters.match_regex(r"^/settings\s+(?P<option>\w+)\s+(?P<value>.+)$"))
    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, option: str, value: str):
        await update.message.reply_text(f"Setting {option} to {value}")
        
MessageHandler()