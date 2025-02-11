from typing import Pattern, Callable, List, Tuple
from telegram import Update
from telegram.ext import ContextTypes
import re
from src.core.registry.registry_base import Registry
from src.handlers.base_handler import BaseHandler


class MessageRegistry:
    _instances = {}  # 用字典存储每个类的实例
    _handlers: List[Tuple[Pattern, Callable]] = []  # 存储所有的处理器

    def __new__(cls):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    @classmethod
    def register(cls, pattern: str):
        """
        装饰器，用于注册消息处理器
        pattern: 正则表达式模式，用于匹配消息文本
        示例：
        @registry.register(r"^/start")
        async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            pass
        """
        regex = re.compile(pattern, re.IGNORECASE)  # 默认不区分大小写

        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # 获取函数所属的类名
                if hasattr(func, '__qualname__'):
                    class_name = func.__qualname__.split('.')[0]
                    # 从 Registry 获取实例
                    instance = Registry.get_handler(class_name)
                    if instance:
                        # 使用实例调用方法
                        bound_method = getattr(instance, func.__name__)
                        return await bound_method(*args, **kwargs)
                return await func(*args, **kwargs)
            
            cls._handlers.append((regex, wrapper))
            return func
        return decorator

    @classmethod
    async def dispatch(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """分发消息到对应的处理器"""
        if not update.message or (not update.message.text and not update.message.caption):
            return

        text = update.message.text or update.message.caption
        
        for pattern, handler in cls._handlers:
            match = pattern.match(text)
            if match:
                try:
                    # 将正则匹配的分组作为关键字参数传递给处理器
                    kwargs = match.groupdict()
                    await handler(update, context, **kwargs)
                    return
                except Exception as e:
                    print(f"Error handling message: {e}")
