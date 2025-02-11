from src.handlers.base_handler import BaseHandler
from telegram import Update
from telegram.ext import ContextTypes


# 具体的处理器类
class MenuHandler(BaseHandler):
    def __init__(self):
        super().__init__()  # 确保调用父类的__init__

    async def handle_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 处理菜单逻辑
        pass
    
# 在应用启动时初始化
MenuHandler()