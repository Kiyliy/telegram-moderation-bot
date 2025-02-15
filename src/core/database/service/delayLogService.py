import asyncio
import json
from typing import Dict, Optional, List, Literal
import uuid
import traceback
import time
import random
from src.core.logger import logger
from core.database.db.delay_logs import (
    UserLogsDatabase,
    UserLogsEntry,
)
from src.core.tools.task_keeper import TaskKeeper


class FullyMatchedDelayedLoggingSystem:
    cache: Dict[str, Dict] = {}
    lock = asyncio.Lock()

    def __init__(
        self,
        db: UserLogsDatabase = None,
        max_cache_time: int = 300,
        scan_probability: float = 0.1,
    ):
        # self.cache = {}
        self.max_cache_time = max_cache_time
        self.scan_probability = scan_probability
        # self.lock = asyncio.Lock()
        self.max_time_between_scans = 60  # 最长60秒必定扫描一次
        self.last_scan_time = time.time()

    async def create_log(
        self,
        user_id: int,
        chat_id: int,
        message_id: int = None,
        log_type: Literal["消费", "兑换", "系统", "其它", "签到"] = None,
        user_message: Optional[str] = None,
        msg_history: Optional[str] = None,
        bot_response: Optional[str] = None,
        caption: Optional[str] = None,
        point_change: Optional[Dict] = None,
        vip_days_change: Optional[int] = None,
        extra_data: Optional[Dict] = None,
    ) -> str:
        """
        创建一个延迟log
        为了兼容, 来自system的log可以给一个user_id = 0000
        -------
        param: user_id
        param: chat_id
        param: message_id
        param: log_type: Literal["消费","兑换","系统","其它","签到"] -> 消费单独一张表
        param: user_message: user调用命令所发送的消息
        -------
        param: msg_history: user传递给chat的消息
        param: bot_response: bot回复的消息
        param: caption: 备注信息
        param: point_change: dict{'daily': int, "vip": int, "permanent": int}
        param: vip_days_change: int
        param: extra_data: {"bot_response_time": int, "database_time": int}

        return: session_id
        """
        session_id = str(uuid.uuid4())
        current_time = int(time.time())
        log_entry = {
            "session_id": session_id,
            "user_id": user_id,
            "chat_id": chat_id,
            "message_id": message_id,
            "log_type": log_type,
            "user_message": user_message,
            "msg_history": msg_history,
            "bot_response": bot_response,
            "caption": caption,
            "point_change": point_change if point_change else None,
            "vip_days_change": vip_days_change if vip_days_change else None,
            "extra_data": extra_data if extra_data else None,
            "created_at": current_time,
            "updated_at": current_time,
        }
        async with self.lock:
            self.cache[session_id] = log_entry

        # 0.1概率, 扫描一次, 最多60s必定扫描, 防止日志堆积
        if (
            random.random() < self.scan_probability
            or current_time - self.last_scan_time > self.max_time_between_scans
        ):
            await self._scan_and_flush_cache()
            self.last_scan_time = current_time

        return session_id

    async def update_log(self, session_id: str, **kwargs):
        """
        使用session_id覆盖之前的日志信息

        param: session_id
        --------可选(create_log时已记录)-----------------
        param: user_id
        param: chat_id
        param: message_id
        param: log_type: Literal["消费","兑换","系统","其它","签到"]
        param: user_message: user调用命令所发送的消息
        --------可选(create_log时已记录)------------------
        param: msg_history: user传递给chat的消息
        param: bot_response: bot回复的消息
        param: caption: 备注信息
        param: point_change: dict{'daily': int, "vip": int, "permanent": int}
        param: vip_days_change: int
        param: extra_data: {"bot_response_time": int, "database_time": int}
        """
        try:
            async with self.lock:
                if session_id in self.cache:
                    log_entry = self.cache[session_id]
                    for key, value in kwargs.items():
                        if key in log_entry:
                            if (
                                key in ["point_change", "extra_data"]
                                and value is not None
                            ):
                                log_entry[key] = json.dumps(value)
                            else:
                                log_entry[key] = value
                    log_entry["updated_at"] = int(time.time())
                else:
                    logger.error(
                        f"Attempt to update non-existent log entry: {session_id}"
                    )
                    print(
                        f"Attempt to update non-existent log entry: {session_id},{self.cache}"
                    )
        except Exception as err:
            logger.error(
                f"An error occurred when try to update the log{err}", exc_info=True
            )
            print(f"An error occurred when try to update a log{traceback.format_exc()}")

    async def commit_log(self, session_id: str):
        """
        提交任务, 这个任务将被写入数据库
        param: session_id

        """
        async with self.lock:
            if session_id in self.cache:
                await self._write_to_database([session_id])
            else:
                logger.error(f"Attempt to commit non-existent log entry: {session_id}")
                print(f"Attempt to commit non-existent log entry: {session_id}")

    async def _write_to_database(self, session_ids: List[str]):
        """
        将日志批量写入数据库,
        如果log_type == "系统" or "兑换" 进入db
        如果log_type == "消费" or 其它 or 签到 , 进入ConsumptionDB
        """
        try:
            log_entries = []
            # 1. 将session_id加入到session_ids中
            for session_id in session_ids:
                log_data = self.cache[session_id]
                log_entry = UserLogsEntry.from_dict(log_data)
                log_entries.append(log_entry)

            # 2. 创建相关任务
            if log_entries:
                TaskKeeper.create_task(self.db.insert_logs(log_entries))

            # 3. 删除缓存
            for session_id in session_ids:
                del self.cache[session_id]  # 删除这条日志

        except Exception as e:
            logger.error(f"Error writing logs to database: {str(e)}", exc_info=True)
            print(f"Error writing logs to database: {traceback.format_exc()}")

    async def _scan_and_flush_cache(self):
        """
        扫描缓存, 对于超时任务进行提交数据库
        """
        current_time = int(time.time())
        to_flush = []
        async with self.lock:
            for session_id, log_data in list(self.cache.items()):
                if current_time - log_data["created_at"] >= self.max_cache_time:
                    to_flush.append(session_id)

            if to_flush:
                await self._write_to_database(to_flush)
