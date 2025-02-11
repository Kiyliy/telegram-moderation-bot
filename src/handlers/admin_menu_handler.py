from src.handlers.base_handler import BaseHandler
from telegram import Update
from telegram.ext import ContextTypes
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.core.registry.CallbackRegistry import CallbackRegistry

# 具体的处理器类
class MenuHandler(BaseHandler):
    def __init__(self):
        super().__init__()  # 确保调用父类的__init__
        
    @CallbackRegistry.register(r"^option")
    async def test(self, update, context):
        print(f"receive msg {update.callback_query}")

    @MessageRegistry.register(MessageFilters.match_prefix(['/start', 'help', '/settings']))
    async def handle_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 处理菜单逻辑
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton("选项1", callback_data="option1"),
                InlineKeyboardButton("选项2", callback_data="option2")
            ],
            [
                InlineKeyboardButton("帮助", callback_data="help"),
                InlineKeyboardButton("设置", callback_data="settings")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="请选择以下选项:",
            reply_markup=reply_markup
        )
    
# 在应用启动时初始化
MenuHandler()