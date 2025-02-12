from typing import Optional, List, Dict, Any
from src.core.database.models.db_moderation_log import ModerationLog
from src.core.database.db.base_database import BaseDatabase
import os


class ModerationLogDatabase(BaseDatabase):
    """审核日志数据库操作类"""
    
    def _initialize(self):
        super()._initialize()
        self.table_name = "moderation_logs"
        if os.getenv("SKIP_DB_INIT", "False") != "True":
            print("创建审核日志表...")
            self._create_table()
        else:
            print("跳过创建审核日志表")
        
    def _create_table(self) -> None:
        """创建表"""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            chat_id BIGINT NOT NULL,
            message_id BIGINT,
            content TEXT,
            content_type VARCHAR(20) NOT NULL,
            violation_type VARCHAR(50),
            action VARCHAR(20),
            action_duration INT,
            operator_id BIGINT,
            is_auto BOOLEAN DEFAULT TRUE,
            confidence FLOAT,
            has_appeal BOOLEAN DEFAULT FALSE,
            appeal_time INT,
            appeal_reason TEXT,
            review_status VARCHAR(20) DEFAULT 'pending',
            review_time INT,
            reviewer_id BIGINT,
            created_at INT NOT NULL,
            updated_at INT NOT NULL,
            INDEX idx_user_chat (user_id, chat_id),
            INDEX idx_review_status (review_status),
            INDEX idx_created_at (created_at),
            INDEX idx_violation_type (violation_type),
            INDEX idx_has_appeal (has_appeal)
        )
        """
        self.execute(sql)
        
    async def add_log(self, log: ModerationLog) -> Optional[int]:
        """添加日志"""
        sql = f"""
        INSERT INTO {self.table_name} (
            user_id, chat_id, message_id, content, content_type,
            violation_type, action, action_duration, operator_id,
            is_auto, confidence, has_appeal, appeal_time, appeal_reason,
            review_status, review_time, reviewer_id, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            log.user_id,
            log.chat_id,
            log.message_id,
            log.content,
            log.content_type,
            log.violation_type,
            log.action,
            log.action_duration,
            log.operator_id,
            log.is_auto,
            log.confidence,
            log.has_appeal,
            log.appeal_time,
            log.appeal_reason,
            log.review_status,
            log.review_time,
            log.reviewer_id,
            log.created_at,
            log.updated_at
        )
        return await self.execute_async(sql, values)
        
    async def update_review(
        self,
        log_id: int,
        review_status: str,
        reviewer_id: int,
        review_time: int
    ) -> bool:
        """更新审核状态"""
        sql = f"""
        UPDATE {self.table_name}
        SET review_status = %s,
            reviewer_id = %s,
            review_time = %s,
            updated_at = %s
        WHERE id = %s
        """
        result = await self.execute_async(
            sql,
            (review_status, reviewer_id, review_time, review_time, log_id)
        )
        return bool(result)
        
    async def update_appeal(
        self,
        log_id: int,
        appeal_reason: str,
        appeal_time: int
    ) -> bool:
        """更新申诉信息"""
        sql = f"""
        UPDATE {self.table_name}
        SET has_appeal = TRUE,
            appeal_reason = %s,
            appeal_time = %s,
            updated_at = %s
        WHERE id = %s
        """
        result = await self.execute_async(
            sql,
            (appeal_reason, appeal_time, appeal_time, log_id)
        )
        return bool(result)
        
    async def get_pending_logs(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[ModerationLog]:
        """获取待审核的日志"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE review_status = 'pending'
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        rows = await self.fetch_all(sql, (limit, offset))
        return [ModerationLog.from_list(row) for row in rows]
        
    async def get_pending_appeals(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[ModerationLog]:
        """获取待处理的申诉"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE has_appeal = TRUE AND review_status = 'pending'
        ORDER BY appeal_time DESC
        LIMIT %s OFFSET %s
        """
        rows = await self.fetch_all(sql, (limit, offset))
        return [ModerationLog.from_list(row) for row in rows]
        
    async def get_logs_by_user(
        self,
        user_id: int,
        chat_id: Optional[int] = None,
        limit: int = 10
    ) -> List[ModerationLog]:
        """获取用户的审核日志"""
        if chat_id:
            sql = f"""
            SELECT * FROM {self.table_name}
            WHERE user_id = %s AND chat_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            rows = await self.fetch_all(sql, (user_id, chat_id, limit))
        else:
            sql = f"""
            SELECT * FROM {self.table_name}
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            rows = await self.fetch_all(sql, (user_id, limit))
        return [ModerationLog.from_list(row) for row in rows]
        
    async def get_logs_by_chat(
        self,
        chat_id: int,
        limit: int = 10
    ) -> List[ModerationLog]:
        """获取群组的审核日志"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE chat_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        rows = await self.fetch_all(sql, (chat_id, limit))
        return [ModerationLog.from_list(row) for row in rows]
        
    async def get_logs_by_type(
        self,
        violation_type: str,
        limit: int = 10
    ) -> List[ModerationLog]:
        """获取特定类型的审核日志"""
        sql = f"""
        SELECT * FROM {self.table_name}
        WHERE violation_type = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        rows = await self.fetch_all(sql, (violation_type, limit))
        return [ModerationLog.from_list(row) for row in rows]
        
    async def get_review_stats(self) -> Dict[str, Any]:
        """获取审核统计"""
        sql = f"""
        SELECT 
            review_status,
            COUNT(*) as count,
            COUNT(DISTINCT user_id) as user_count,
            COUNT(DISTINCT chat_id) as chat_count,
            AVG(CASE WHEN confidence IS NOT NULL THEN confidence ELSE 0 END) as avg_confidence
        FROM {self.table_name}
        GROUP BY review_status
        """
        rows = await self.fetch_all_dict(sql)
        return {
            row['review_status']: {
                'count': row['count'],
                'user_count': row['user_count'],
                'chat_count': row['chat_count'],
                'avg_confidence': row['avg_confidence']
            } for row in rows
        } 