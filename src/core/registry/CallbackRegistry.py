from typing import Dict, Type, Any
from telegram import Update
from telegram.ext import ContextTypes
import re
from typing import Callable
from src.core.registry.registry_base import Registry


# 回调注册器
class CallbackRegistry:
    _instance = None
    _handlers = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, pattern: str):
        """装饰器，用于注册回调处理器"""
        regex = re.compile(pattern)
        
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # 获取函数所属的类名
                if hasattr(func, '__qualname__'):
                    class_name = func.__qualname__.split('.')[0]
                    # 从Registry获取实例
                    instance = Registry.get_handler(class_name)
                    if instance:
                        bound_method = getattr(instance, func.__name__)
                        return await bound_method(*args, **kwargs)
                return await func(*args, **kwargs)
            
            cls._handlers.append((regex, wrapper))
            return func
        return decorator

    async def dispatch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """分发回调到对应的处理器"""
        if not update.callback_query:
            return
            
        query = update.callback_query
        data = query.data
        
        for pattern, handler in self._handlers:
            if pattern.match(data):
                try:
                    await handler(update, context)
                finally:
                    await query.answer()
                return