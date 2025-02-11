from typing import Dict, Any



class Registry:
    _instance = None
    _handlers: Dict[str, Any] = {}  # 使用类名作为key

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def add_handler(cls, instance: Any):
        """注册处理器实例"""
        class_name = instance.__class__.__name__
        cls._handlers[class_name] = instance
        return instance

    @classmethod
    def get_handler(cls, class_name: str):
        """获取处理器实例"""
        return cls._handlers.get(class_name)