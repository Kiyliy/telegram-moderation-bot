from src.handlers.base_handler import BaseHandler
from telegram import Update
from telegram.ext import ContextTypes


# 具体的处理器类
class MenuHandler(BaseHandler):
    def __init__(self):
        super().__init__()  # 确保调用父类的__init__

    # 注册Callback
    @CallbackRegistry.register(r"^option")
    async def test(self, update, context):
        print(f"receive msg {update.callback_query}")

    # 注册消息命令前缀
    @MessageRegistry.register(MessageFilters.match_prefix(['/start', '/help', '/settings']))
    async def handle_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 处理菜单逻辑
        print(f"receive msg {update}")
    
# 在应用启动时初始化 -> 此时会自动执行init函数, 然后会自动注册自己的实例
MenuHandler()