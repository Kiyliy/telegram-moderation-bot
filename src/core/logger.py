# logger.py
import logging
from logging.handlers import RotatingFileHandler
import os

# 创建日志目录
os.makedirs("data/log/info", exist_ok=True)
os.makedirs("data/log/error", exist_ok=True)


# 配置日志处理器
def setup_logger(
    name, info_log_file, error_log_file, max_size=20 * 1024 * 1024, backup_count=10
):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Info level handler
    info_handler = RotatingFileHandler(
        info_log_file, maxBytes=max_size, backupCount=backup_count, encoding="utf-8"
    )
    info_handler.setLevel(logging.INFO)
    info_formatter = logging.Formatter(
        "[INFO] %(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    info_handler.setFormatter(info_formatter)

    # Error level handler
    error_handler = RotatingFileHandler(
        error_log_file, maxBytes=max_size, backupCount=backup_count, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        "[ERROR] %(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    error_handler.setFormatter(error_formatter)

    # Adding handlers to the logger
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)

    return logger


# 创建logger实例
logger = setup_logger(
    "member_system_logger", "data/log/info/info.log", "data/log/error/error.log"
)
