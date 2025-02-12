import datetime
import os
import time
from src.core.logger import logger
import mysql.connector
from dotenv import load_dotenv
import aiomysql
from typing import Dict, Any, Optional, List
import traceback
from src.core.database.models.db_user import UserInfo
from src.core.database.db.base_database import BaseDatabase
from src.core.config.config import Config
from data.ConfigKeys import ConfigKeys

class UserDatabase(BaseDatabase):
    """用户数据库操作类"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "users"
        if os.getenv("SKIP_DB_INIT", "False") != "True":
            print("创建用户表...")
            self._create_table()
        else:
            print("跳过创建用户表")

    def _create_table(self) -> None:
        """创建表"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT UNIQUE NOT NULL,
            chat_id BIGINT,
            user_name TEXT,
            display_name TEXT,
            is_blocked BOOL NOT NULL DEFAULT false,
            daily_point_balance INT NOT NULL DEFAULT 0,
            daily_point_last_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vip_point_balance INT NOT NULL DEFAULT 0,
            vip_point_expired_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            permanent_point_balance INT NOT NULL DEFAULT 0,
            has_used_ai BOOL NOT NULL DEFAULT false,
            invited_by_user_id BIGINT,
            language VARCHAR(10) NOT NULL DEFAULT 'en',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_chat_id (chat_id),
            INDEX idx_created_at (created_at),
            INDEX idx_updated_at (updated_at)
        )
        """
        self.execute(sql)

    async def add_user(
        self,
        user_id: int,
        user_name: str,
        display_name: str,
        chat_id: Optional[int] = None,
        invited_by_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """添加用户"""
        sql = f"""
        INSERT INTO {self.table_name} (
            user_id, user_name, display_name, chat_id, 
            daily_point_balance, permanent_point_balance, invited_by_user_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            user_id,
            user_name,
            display_name,
            chat_id,
            Config.get_config(ConfigKeys.database.DAILY_POINTS),
            Config.get_config(ConfigKeys.database.PERMANENT_POINTS),
            invited_by_user_id,
        )
        result = await self.execute_async(sql, values)
        return self.format_result(
            bool(result),
            f"User {user_id} {'added' if result else 'failed to add'}"
        )
        
    async def get_user_info(self, user_id: int) -> Optional[UserInfo]:
        """获取用户信息"""
        sql = f"""
        SELECT id,
            user_id,
            chat_id,
            user_name,
            display_name,
            is_blocked,
            daily_point_balance,
            UNIX_TIMESTAMP(daily_point_last_reset_at) AS daily_point_last_reset_at,
            vip_point_balance,
            UNIX_TIMESTAMP(vip_point_expired_date) AS vip_point_expired_date,
            permanent_point_balance,
            has_used_ai,
            invited_by_user_id,
            language,
            UNIX_TIMESTAMP(created_at) AS created_at,
            UNIX_TIMESTAMP(updated_at) AS updated_at
        FROM {self.table_name} 
        WHERE user_id = %s
        """
        row = await self.fetch_one(sql, (user_id,))
        return UserInfo.from_list(row) if row else None
        
    async def update_display_info(
        self, 
        user_id: int, 
        user_name: str, 
        display_name: str
    ) -> Dict[str, Any]:
        """更新用户显示信息"""
        sql = f"""
        UPDATE {self.table_name} 
        SET user_name = %s, display_name = %s 
        WHERE user_id = %s
        """
        result = await self.execute_async(sql, (user_name, display_name, user_id))
        return self.format_result(
            bool(result),
            f"User {user_id} display info {'updated' if result else 'failed to update'}"
        )
        
    async def update_ai_status(
        self, 
        user_id: int, 
        has_used_ai: bool
    ) -> Dict[str, Any]:
        """更新用户AI使用状态"""
        sql = f"""
        UPDATE {self.table_name} 
        SET has_used_ai = %s 
        WHERE user_id = %s
        """
        result = await self.execute_async(sql, (has_used_ai, user_id))
        return self.format_result(
            bool(result),
            f"User {user_id} AI status {'updated' if result else 'failed to update'}"
        )
        
    async def update_invited_by(
        self, 
        user_id: int, 
        invited_by_user_id: int
    ) -> Dict[str, Any]:
        """更新用户邀请者ID"""
        sql = f"""
        UPDATE {self.table_name} 
        SET invited_by_user_id = %s 
        WHERE user_id = %s
        """
        result = await self.execute_async(sql, (invited_by_user_id, user_id))
        return self.format_result(
            bool(result),
            f"User {user_id} invited by user {invited_by_user_id} {'updated' if result else 'failed to update'}"
        )
        
    async def update_balance(
        self,
        user_id: int,
        daily_points: int,
        vip_points: int,
        vip_expired_date: int,
        permanent_points: int,
    ) -> Dict[str, Any]:
        """更新用户积分余额"""
        sql = f"""
        UPDATE {self.table_name} 
        SET daily_point_balance = %s,
            vip_point_balance = %s,
            vip_point_expired_date = FROM_UNIXTIME(%s),
            permanent_point_balance = %s
        WHERE user_id = %s
        """
        values = (
            daily_points,
            vip_points,
            vip_expired_date,
            permanent_points,
            user_id,
        )
        result = await self.execute_async(sql, values)
        return self.format_result(
            bool(result),
            f"User {user_id} balance {'updated' if result else 'failed to update'}"
        )

    async def reset_daily_balance(
        self, 
        user_id: int, 
        amount: int = 0
    ) -> Dict[str, Any]:
        """重置用户每日积分"""
        sql = f"""
        UPDATE {self.table_name} 
        SET daily_point_balance = %s,
            daily_point_last_reset_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
        """
        result = await self.execute_async(sql, (amount, user_id))
        return self.format_result(
            bool(result),
            f"User {user_id} daily balance {'reset' if result else 'failed to reset'}"
        )
        
    async def get_language(self, user_id: int) -> Optional[str]:
        """获取用户语言设置"""
        sql = f"""
        SELECT language 
        FROM {self.table_name} 
        WHERE user_id = %s
        """
        row = await self.fetch_one(sql, (user_id,))
        return row[0] if row else None
        
    async def update_language(
        self, 
        user_id: int, 
        language: str
    ) -> Dict[str, Any]:
        """更新用户语言设置"""
        sql = f"""
        UPDATE {self.table_name} 
        SET language = %s 
        WHERE user_id = %s
        """
        result = await self.execute_async(sql, (language, user_id))
        return self.format_result(
            bool(result),
            f"User {user_id} language {'updated' if result else 'failed to update'}"
        )
