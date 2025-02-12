import os
import mysql.connector
import aiomysql
from typing import Optional, List, Any, Dict, Tuple
from src.core.logger import logger
import traceback
from dotenv import load_dotenv

class BaseDatabase:
    """
    数据库基类
    """
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(BaseDatabase, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 从环境变量获取配置
        self.DB_CONFIG = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_APP_USER"),
            "password": os.getenv("DB_APP_USER_PASSWORD"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "db": os.getenv("DB_APP_NAME"),
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", 10)),
        }
        
        # 表名（子类需要设置）
        self.table_name = None
        
    def execute(self, sql: str, params: tuple = None) -> Optional[int]:
        """
        执行SQL（同步），主要用于创建表等操作
        返回最后插入的ID或受影响的行数
        """
        try:
            with mysql.connector.connect(**self.DB_CONFIG) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    return cursor.lastrowid or cursor.rowcount
        except Exception as e:
            logger.error(f"执行SQL出错: {sql}, {str(e)}", exc_info=True)
            print(f"执行SQL出错: {sql}\n{traceback.format_exc()}")
            return None
            
    async def execute_async(self, sql: str, params: tuple = None) -> Optional[int]:
        """
        执行SQL（异步）
        返回最后插入的ID或受影响的行数
        """
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
                    await conn.commit()
                    return cursor.lastrowid or cursor.rowcount
        except Exception as e:
            logger.error(f"执行SQL出错: {sql}, {str(e)}", exc_info=True)
            print(f"执行SQL出错: {sql}\n{traceback.format_exc()}")
            return None
            
    async def fetch_one(self, sql: str, params: tuple = None) -> Optional[tuple]:
        """查询单条记录"""
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
                    return await cursor.fetchone()
        except Exception as e:
            logger.error(f"查询出错: {sql}, {str(e)}", exc_info=True)
            print(f"查询出错: {sql}\n{traceback.format_exc()}")
            return None
            
    async def fetch_all(self, sql: str, params: tuple = None) -> List[tuple]:
        """查询多条记录"""
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(f"查询出错: {sql}, {str(e)}", exc_info=True)
            print(f"查询出错: {sql}\n{traceback.format_exc()}")
            return []
            
    async def fetch_dict(self, sql: str, params: tuple = None) -> Optional[Dict]:
        """查询单条记录（字典形式）"""
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, params)
                    return await cursor.fetchone()
        except Exception as e:
            logger.error(f"查询出错: {sql}, {str(e)}", exc_info=True)
            print(f"查询出错: {sql}\n{traceback.format_exc()}")
            return None
            
    async def fetch_all_dict(self, sql: str, params: tuple = None) -> List[Dict]:
        """查询多条记录（字典形式）"""
        try:
            async with aiomysql.connect(**self.DB_CONFIG) as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(sql, params)
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(f"查询出错: {sql}, {str(e)}", exc_info=True)
            print(f"查询出错: {sql}\n{traceback.format_exc()}")
            return []
            
    def format_result(self, success: bool, message: str, data: Any = None) -> Dict:
        """格式化返回结果"""
        result = {
            "success": success,
            "message": message,
            "data": None
        }
        if data is not None:
            result["data"] = data
        return result 