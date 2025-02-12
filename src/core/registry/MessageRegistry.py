from telegram import Update
from telegram.ext import ContextTypes
# from telegram.ext import ApplicationHandlerStop
from typing import List, Callable, Tuple
from src.core.registry.registry_base import Registry_Base  # 导入基础注册器
import traceback
import asyncio
from src.core.database.InfoSaver import InfoSaver
from src.core.tools.task_keeper import TaskKeeper
class MessageRegistry:
    _instance = None
    _handlers: List[Tuple[Callable, Callable]] = []  # [(filter_func, handler_func), ...]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    @classmethod
    def register(cls, message_filter: Callable = None):
        """
        装饰器，用于注册消息处理器
        message_filter: 消息过滤器函数
        pattern: 正则表达式模式（如果提供，会自动创建文本匹配过滤器）
        
        使用示例:
        1. 使用命令过滤器:
        @MessageRegistry.register(MessageFilters.is_command(['start', 'help']))
        async def handle_command(self, update, context):
            pass

        2. 使用正则匹配:
        @MessageRegistry.register(pattern=r"^我要申诉\s*(?P<id>\d+)?$")
        async def handle_appeal(self, update, context):
            match_groups = update.message._match_groups  # 获取正则匹配组
            appeal_id = match_groups.get('id')
            pass
        
        3. 使用自定义过滤器:
        @MessageRegistry.register(lambda update: update.message.photo)
        async def handle_photo(self, update, context):
            pass
        """
        def decorator(func: Callable):
            # 获取处理器信息
            handler_name = func.__name__
            class_name = func.__qualname__.split('.')[0]
            
            # 提取过滤器信息
            if hasattr(message_filter, '__closure__') and message_filter.__closure__:
                for cell in message_filter.__closure__:
                    contents = cell.cell_contents
                # 打印出来
                print(f"[Register] {class_name}.{handler_name} -> {contents}")

            async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
                if hasattr(func, '__qualname__'):
                    class_name = func.__qualname__.split('.')[0]
                    # 从 Registry 获取实例
                    instance = Registry_Base.get_handler(class_name)
                    if instance:
                        method = func.__get__(instance, instance.__class__)  # 创建绑定方法
                        return await method(update, context)
                return await func(update, context)
            
            cls._handlers.append((message_filter, wrapper))
            return func
        return decorator

    @classmethod
    async def dispatch(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """分发消息到对应的处理器"""
        TaskKeeper.create_task(InfoSaver.info_save(update, context))
        for filter_func, handler in cls._handlers:
            try:
                if filter_func and filter_func(update):
                    await handler(update, context)
                    return
            except Exception as e:
                print(f"Error in message handler: {e}, {traceback.format_exc()}")
        print("[DEV] No handler found for update:", update)
