from abc import ABC, ABCMeta
from typing import Dict, TypeVar, Optional, Type, Any
from pathlib import Path
import json

T = TypeVar('T')

class CommandMeta(ABCMeta):
    """
    命令元类，用于实现单例模式和自动注册
    当一个命令类被定义时，就会自动创建它的实例并注册到工厂中
    """
    _instances: Dict[str, object] = {}
    _command_paths: Dict[str, str] = {}  # 存储命令类与其配置路径的映射
    _command_configs: Dict[str, Dict[str, Any]] = {}  # 存储命令配置
    
    def __new__(mcs, name: str, bases: tuple, attrs: dict):
        """
        在类定义时被调用
        例如：当解释器执行到 'class StartCommand(CommandBase):' 时
        """
        # 创建类
        cls = super().__new__(mcs, name, bases, attrs)
        
        # 如果不是 CommandBase 本身，而是它的子类，就创建实例
        if name != 'CommandBase':
            # 获取命令路径
            if hasattr(cls, '_command_path'):
                cmd_path = cls._command_path
            else:
                # 从类名推断命令路径
                cmd_name = name.replace('Command', '').lower()
                cmd_path = f'data/commands/{cmd_name}'
            
            # 存储命令路径
            mcs._command_paths[name] = cmd_path
            
            # 加载命令配置
            config_file = Path(cmd_path) / 'config.json'
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    mcs._command_configs[name] = json.load(f)
            else:
                mcs._command_configs[name] = {}
            
            # 创建实例并注入配置
            instance = cls.__new__(cls)
            instance.__init__(**mcs._command_configs.get(name, {}))
            mcs._instances[name] = instance
            
        return cls
    
    def __call__(cls, *args, **kwargs):
        """
        在类被调用时执行
        例如: StartCommand() 会触发这个方法
        """
        # 直接返回已创建的实例
        return cls._instances.get(cls.__name__)

def command_path(path: str):
    """
    装饰器：指定命令的配置路径
    
    用法：
    @command_path('data/commands/mycommand')
    class MyCommand(CommandBase):
        pass
    """
    def decorator(cls: Type) -> Type:
        cls._command_path = path
        return cls
    return decorator

def command_config(**config):
    """
    装饰器：指定命令的默认配置
    
    用法：
    @command_config(
        allow_groups=True,
        allow_private=True,
        require_admin=False
    )
    class MyCommand(CommandBase):
        pass
    """
    def decorator(cls: Type) -> Type:
        cls._default_config = config
        return cls
    return decorator

class CommandBase(ABC, metaclass=CommandMeta):
    """
    所有命令类的基类
    使用 CommandMeta 作为元类，确保：
    1. 每个命令类只有一个实例（单例模式）
    2. 命令类定义时就创建实例（自动注册）
    3. 可以通过类名获取实例（工厂模式）
    4. 自动加载和注入配置
    """
    
    def __init__(self, **kwargs):
        """
        初始化命令，注入配置
        配置优先级：命令装饰器配置 < config.json配置 < 运行时配置
        """
        # 合并配置
        self._config = {
            **(getattr(self.__class__, '_default_config', {})),  # 装饰器配置
            **kwargs  # 运行时配置（包括从config.json加载的配置）
        }
    
    @staticmethod
    def get_instance(name: str) -> Optional[object]:
        """
        通过类名获取命令类实例
        :param name: 类名，例如 'StartCommand'
        :return: 命令类的实例，如果不存在则返回 None
        """
        return CommandMeta._instances.get(name)
    
    @classmethod
    def get_command_path(cls) -> str:
        """
        获取命令的配置路径
        :return: 配置路径
        """
        return CommandMeta._command_paths.get(cls.__name__, '')
    
    @property
    def config_path(self) -> Path:
        """获取命令配置文件路径"""
        return Path(self.get_command_path()) / 'config.json'
    
    @property
    def i18n_path(self) -> Path:
        """获取命令i18n配置目录路径"""
        return Path(self.get_command_path()) / 'i18n_configs'
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取命令配置"""
        return self._config.copy()
    
    def update_config(self, **kwargs):
        """更新命令配置"""
        self._config.update(kwargs)
