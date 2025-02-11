import pkgutil
from src import handlers  # 改为直接从src导入handlers

def initialize():
    """初始化所有模块"""
    print("Starting initialization...")
    
    # 动态导入 handlers 包下的所有模块
    for _, module_name, _ in pkgutil.iter_modules(handlers.__path__):
        print(f"[Loading] handler module: {module_name}")
        __import__(f'src.handlers.{module_name}', fromlist=[''])
    
    print("Initialization completed")

# 在模块导入时自动执行初始化
initialize()