
from src.core.registry.CallbackRegistry import Registry


# 元类，用于确保每个类只有一个实例
class MetaHandler(type):
    _instances = {}  # 用字典存储每个类的实例

    def __call__(cls, *args, **kwargs):
        # 使用类本身作为key，确保每个类都有自己的实例
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

# 基础处理器类, 使用元类确保每个类只有一个实例, 并自动注册到Registry
class BaseHandler(metaclass=MetaHandler):
    def __init__(self):
        # 在初始化时自动注册
        Registry.add_handler(self)