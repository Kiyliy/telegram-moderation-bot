import mysql.connector
import os
from dotenv import load_dotenv
from src.core.logger import logger


def initialize_database():
    # 加载环境变
    load_dotenv()

    # 从环境变量获取敏感信息
    db_host = os.getenv("DB_HOST")
    root_password = os.getenv("DB_ROOT_PASSWORD")
    db_port = os.getenv("DB_PORT")
    app_db_user = os.getenv("DB_APP_USER")
    app_db_name = os.getenv("DB_APP_NAME")
    app_db_password = os.getenv("DB_APP_USER_PASSWORD")

    conn = None
    cursor = None

    try:
        # 连接到MySQL（不指定数据库）
        conn = mysql.connector.connect(
            host=db_host, user="root", password=root_password, port=db_port
        )

        cursor = conn.cursor()

        # 判断数据库是否存在
        cursor.execute(
            f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{app_db_name}'"
        )
        if cursor.fetchone() is None:
            # 创建新的数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{app_db_name}`")
            conn.commit()
            print(f"数据库 {app_db_name} 已创建")
            logger.info(f"数据库 {app_db_name} 已创建")
        else:
            print(f"数据库 {app_db_name} 已存在")
            logger.info(f"数据库 {app_db_name} 已存在")

        # 判断用户是否存在
        cursor.execute(f"SELECT * FROM mysql.user WHERE user = '{app_db_user}'")
        if cursor.fetchone() is None:
            # 创建新用户，使用 '%' 允许从任何主机连接
            cursor.execute(
                f"CREATE USER IF NOT EXISTS '{app_db_user}'@'%' IDENTIFIED BY '{app_db_password}'"
            )

            # 授予权限
            cursor.execute(
                f"GRANT ALL PRIVILEGES ON `{app_db_name}`.* TO '{app_db_user}'@'%'"
            )

            # 刷新权限
            cursor.execute("FLUSH PRIVILEGES")

            conn.commit()

            print(f"用户 {app_db_user} 已创建并授权(或者已存在)")
            logger.info(f"用户 {app_db_user} 已创建并授权(或者已存在)")
        else:
            print(f"用户 {app_db_user} 已存在")
            logger.info(f"用户 {app_db_user} 已存在")

    except mysql.connector.Error as e:
        print(f"初始化过程中出错: {e}")
        logger.error(f"初始化过程中出错: {e}", exc_info=True)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    initialize_database()
