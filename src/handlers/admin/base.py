from src.handlers.base_handler import BaseHandler
from src.core.config.config import config
from data.ConfigKeys import ConfigKeys as configkey
from typing import Dict, Any
from telegram import CallbackQuery

class AdminBaseHandler(BaseHandler):
    """管理员处理器基类"""
    
    def __init__(self):
        super().__init__()
        self._load_settings()
        
    def _load_settings(self) -> None:
        """加载管理员设置"""
        self.admin_ids = config.get_config(configkey.bot.ADMIN_IDS, [])
        
    def _is_admin(self, user_id: int) -> bool:
        """检查用户是否是管理员"""
        return user_id in self.admin_ids
        
    async def _safe_edit_message(self, query: CallbackQuery, text: str, reply_markup=None) -> None:
        """安全地编辑消息，处理消息未修改的错误"""
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e:
            if "Message is not modified" not in str(e):
                raise 