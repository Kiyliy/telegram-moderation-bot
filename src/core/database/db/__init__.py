# 在 database/__init__.py 中
from .db_init import initialize_database
import os

# 如果是debug模式, 跳过init
if os.getenv("DEBUG","False").lower()=="true":
    print("debug模式跳过数据库的init")
else:
    initialize_database()
