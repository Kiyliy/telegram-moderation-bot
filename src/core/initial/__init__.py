import pkgutil
from src import handlers  # 改为直接从src导入handlers

def _load_submodules(package):
    """递归加载包中的所有模块"""
    for loader, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        full_name = f"{package.__name__}.{module_name}"
        print(f"[Loading] module: {full_name}")
        
        # 导入模块
        module = __import__(full_name, fromlist=[''])
        
        # 如果是包，递归加载其子模块
        if is_pkg:
            _load_submodules(module)

def initialize():
    """初始化所有模块"""
    print("Starting initialization...")
    
    # 递归加载 handlers 包下的所有模块
    _load_submodules(handlers)
    
    print("Initialization completed")

# 在模块导入时自动执行初始化
initialize()