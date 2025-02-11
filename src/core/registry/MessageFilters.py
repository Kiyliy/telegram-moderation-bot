from telegram import Update
from typing import List
import re
import traceback

class MessageFilters:
    COMMANDS = []  # 存储所有注册的命令

    @staticmethod
    def match_prefix(prefixes: List[str]):
        """
        匹配消息前缀
        prefixes: 要匹配的前缀列表，比如 ['start', 'help']
        """
        if not prefixes:
            raise ValueError("Prefixes list cannot be empty")
        
        # 检查重复注册
        for prefix in prefixes:
            if prefix in MessageFilters.COMMANDS:
                print(f"[DEV][ERROR] 前缀 {prefix} 已存在!!!请勿重复注册")
        
        def filter(update: Update) -> bool:
            if not update.message or (not update.message.text and not update.message.caption):
                return False
            text = update.message.text or update.message.caption
            pattern = f"^/?({'|'.join(prefixes)})"
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return True
            return False
        
        MessageFilters.COMMANDS.extend(prefixes)
        return filter

    @staticmethod
    def match_regex(pattern: str):
        """
        正则表达式匹配
        pattern: 正则表达式模式
        """
        regex = re.compile(pattern, re.IGNORECASE)
        
        def filter(update: Update) -> bool:
            if not update.message or (not update.message.text and not update.message.caption):
                return False
            text = update.message.text or update.message.caption
            match = regex.match(text)
            if match:
                # 存储匹配组供后续使用
                return True
            return False
        
        return filter

    @staticmethod
    def match_media_type(media_types: List[str]):
        """
        匹配媒体类型
        media_types: 媒体类型列表，如 ['photo', 'video']
        """
        def filter(update: Update) -> bool:
            if not update.message:
                return False
            for media_type in media_types:
                if hasattr(update.message, media_type) and getattr(update.message, media_type):
                    return True
            return False
        return filter

    @staticmethod
    def match_bot_added():
        """检测机器人是否被添加到群组"""
        def filter(update: Update) -> bool:
            if not update.message or not update.message.new_chat_members:
                return False
            return any(member.id == update.get_bot().id 
                      for member in update.message.new_chat_members)
        return filter
