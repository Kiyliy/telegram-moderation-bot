from typing import Dict, Any, Optional, List
import time
import uuid
import aiomysql
import mysql.connector
from src.core.logger import logger
from src.core.database.models.db_redemption import RedemptionCodesInfo
from src.core.database.db.base_database import BaseDatabase
import os
import traceback

class RedemptionCodesDatabase(BaseDatabase):
    """兑换码数据库操作类"""
    
    def _initialize(self):
        super()._initialize()
        self.table_name = "redemption_codes"
        if os.getenv("SKIP_DB_INIT", "False") != "True":
            print("创建兑换码表...")
            self._create_table()
        else:
            print("跳过创建兑换码表")

    def _create_table(self) -> None:
        """创建表"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            code VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            user_id BIGINT,
            used_at TIMESTAMP NULL,
            vip_days INT DEFAULT 0,
            vip_points INT DEFAULT 0,
            permanent_point_balance INT DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            caption TEXT,
            INDEX idx_code (code),
            INDEX idx_user_id (user_id),
            INDEX idx_created_at (created_at)
        )
        """
        self.execute(sql)
        
    async def _generate_code(self, length: int = 10) -> Optional[str]:
        """生成唯一兑换码"""
        for _ in range(10):  # 最多尝试10次
            unique_id = str(uuid.uuid4())
            code = unique_id.replace("-", "").upper()
            
            # 调整长度
            if len(code) > length:
                code = code[:length]
            elif len(code) < length:
                code = code.ljust(length, "A")
                
            # 检查唯一性
            if not await self.is_code_exists(code):
                return code
        return None
        
    async def is_code_exists(self, code: str) -> bool:
        """检查兑换码是否存在"""
        sql = f"""
        SELECT code 
        FROM {self.table_name} 
        WHERE code = %s
        """
        row = await self.fetch_one(sql, (code,))
        return bool(row)
        
    async def add_redemption_code(
        self,
        vip_days: int,
        vip_points: int,
        permanent_point_balance: int,
        is_active: bool = True,
        caption: str = "",
    ) -> Dict[str, Any]:
        """添加单个兑换码"""
        code = await self._generate_code()
        if not code:
            return self.format_result(False, "Failed to generate unique code")
            
        sql = f"""
        INSERT INTO {self.table_name} (
            code, vip_days, vip_points, permanent_point_balance, 
            is_active, caption
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            code,
            vip_days,
            vip_points,
            permanent_point_balance,
            is_active,
            caption,
        )
        result = await self.execute_async(sql, values)
        return self.format_result(
            bool(result),
            f"Code {code} {'added' if result else 'failed to add'}",
            {"code": code} if result else None
        )
        
    async def add_many_redemption_codes(
        self,
        number: int,
        vip_days: int,
        vip_points: int,
        permanent_point_balance: int,
        is_active: bool = True,
        code_length: int = 10,
        caption: str = "",
    ) -> Dict[str, Any]:
        """批量添加兑换码"""
        codes = []
        for _ in range(int(number)):
            code = await self._generate_code(code_length)
            if not code:
                continue
            codes.append(code)
            
        if not codes:
            return self.format_result(False, "Failed to generate any unique codes")
            
        sql = f"""
        INSERT INTO {self.table_name} (
            code, vip_days, vip_points, permanent_point_balance, 
            is_active, caption
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = [
            (code, vip_days, vip_points, permanent_point_balance, is_active, caption)
            for code in codes
        ]
        
        success_count = 0
        for value in values:
            result = await self.execute_async(sql, value)
            if result:
                success_count += 1
                
        return self.format_result(
            bool(success_count),
            f"Generated {success_count} of {number} codes",
            {
                "codes": codes[:success_count],
                "total": number,
                "success": success_count,
                "vip_days": vip_days,
                "vip_points": vip_points,
                "permanent_point_balance": permanent_point_balance
            }
        )
        
    async def get_redemption_code_info(self, code: str) -> Optional[RedemptionCodesInfo]:
        """获取兑换码信息"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE code = %s
        """
        row = await self.fetch_one(sql, (code,))
        return RedemptionCodesInfo.from_list(row) if row else None
        
    async def use_redemption_code(
        self, 
        code: str, 
        user_id: int
    ) -> Dict[str, Any]:
        """使用兑换码"""
        # 先检查兑换码状态
        info = await self.get_redemption_code_info(code)
        if not info:
            return self.format_result(False, "Code not found")
            
        if not info.is_active:
            return self.format_result(False, "Code is not active")
            
        if info.user_id:
            return self.format_result(False, "Code has already been used")
            
        # 更新兑换码状态
        sql = f"""
        UPDATE {self.table_name}
        SET user_id = %s,
            used_at = CURRENT_TIMESTAMP,
            is_active = FALSE
        WHERE code = %s AND user_id IS NULL
        """
        result = await self.execute_async(sql, (user_id, code))
        if not result:
            return self.format_result(False, "Failed to use code")
            
        return self.format_result(
            True,
            f"Code {code} used successfully",
            {
                "vip_days": info.vip_days,
                "vip_points": info.vip_points,
                "permanent_point_balance": info.permanent_point_balance
            }
        )
        
    async def delete_code(self, code: str) -> Dict[str, Any]:
        """删除兑换码"""
        sql = f"""
        DELETE FROM {self.table_name}
        WHERE code = %s
        """
        result = await self.execute_async(sql, (code,))
        return self.format_result(
            bool(result),
            f"Code {code} {'deleted' if result else 'failed to delete'}"
        )