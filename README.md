# telegram-moderation-bot
a telegram moderation bot based on chatgpt

使用ChatGPT的接口, 进行telegram的群组审核

# 需求分析
1. 总是有用户在群里捣乱, 然后弄一堆黄色/血腥的东西, 容易让群组被封
2. 所以需要针对, 群组的图片/视频进行审核
3. 相关的日志记录
4. 及时的, 将信息反馈给管理员

# 概要设计
1. 获取群组信息, 只接受图片/视频/命令消息
2. 获取到图片过后, 调用ChatGPT的API, 进行审核
    2.1 这里进行抽象, 因为后面可能会支持别的审核接口
    2.2 支持多种审核维度：色情、暴力、政治敏感等
    2.3 支持自定义审核规则和敏感度阈值
3. 如果审核不通过, 则将用户的消息删除, 并发送一个警告消息
    3.1 您发送的消息审核不通过, 此消息已被删除, 如果你认为有任何问题, 可以点击申诉
    3.2 按钮, 申诉, 重审
    3.3 向管理员发送一个告警消息, 允许管理员, 对此进行处理
        3.3.1 通过 , 表明ai误判, 重新发送这个消息
        3.3.2 惩罚用户
            3.3.2.1 禁言用户 -> 按钮指定时长
            3.3.2.2 踢出用户
            3.3.2.3 拉黑用户
4. 如果审核通过, 则无反应/返回一个msg, 管理员可进行设置
5. 管理功能
    管理员使用自定义键盘, 进行管理
    5.1 支持管理员配置审核规则
    5.2 支持查看审核日志和统计信息
    5.3 支持批量处理违规消息
    5.4 支持自定义警告消息模板


# 详细设计

## 1. 系统架构

### 1.1 核心模块
```
core/
  ├── command_base.py      # 命令基类
  ├── callback_registry.py # 回调注册器
  ├── message_handler.py   # 消息处理器
  ├── content_moderator/   # 内容审核模块
  │   ├── moderator_base.py
  │   ├── chatgpt_moderator.py
  │   └── moderator_factory.py
  ├── storage/            # 存储模块
  │   ├── storage_base.py
  │   ├── mongodb_storage.py
  │   └── storage_factory.py


commands/
  ├── admin_commands.py   # 管理员命令
  ├── user_commands.py    # 用户命令
  └── callback_handlers.py # 回调处理器

models/
  ├── group.py
  ├── audit_log.py
  ├── user_status.py
  └── message.py
```

### 1.2 设计模式应用
1. 命令模式 (Command Pattern)
   ```python
   class CommandBase:
       _instances = {}
       
       @classmethod
       def get_instance(cls, class_name: str):
           return cls._instances.get(class_name)
           
       def __init__(self):
           class_name = self.__class__.__name__
           self.__class__._instances[class_name] = self
           
       async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
           raise NotImplementedError
   
   class AdminCommand(CommandBase):
       async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
           # 实现管理员命令逻辑
           pass
   ```

2. 工厂模式 (Factory Pattern)
   ```python
   class ModeratorFactory:
       @staticmethod
       def create_moderator(moderator_type: str) -> ContentModeratorBase:
           if moderator_type == "chatgpt":
               return ChatGPTModerator()
           # 可扩展其他审核器
           raise ValueError(f"Unknown moderator type: {moderator_type}")
   ```

3. 单例模式 (Singleton Pattern)
   ```python
   class CallbackRegistry:
       _instance = None
       _handlers = []
       
       def __new__(cls):
           if cls._instance is None:
               cls._instance = super().__new__(cls)
           return cls._instance
   ```

### 1.3 数据模型
```python
class Group:
    group_id: str
    settings: dict
    admin_ids: List[int]
    moderator_type: str
    created_at: datetime
    updated_at: datetime

class AuditLog:
    message_id: str
    group_id: str
    user_id: int
    content_type: str
    content_url: str
    audit_result: bool
    audit_score: float
    audit_time: datetime
    action_taken: str
    moderator_type: str
    appeal_status: str

class UserStatus:
    user_id: int
    group_id: str
    username: str
    violation_count: int
    last_violation: datetime
    status: str  # normal/muted/banned
    mute_until: datetime
    created_at: datetime
    updated_at: datetime

class Message:
    message_id: str
    group_id: str
    user_id: int
    content_type: str
    content_url: str
    created_at: datetime
```

## 2. 核心流程

### 2.1 消息处理流程
```python
class MessageHandler:
    def __init__(self):
        self.queue = QueueFactory.create_queue()
        self.moderator = ModeratorFactory.create_moderator("chatgpt")
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 1. 验证消息类型
        if not self._is_valid_content(update.message):
            return
            
        # 2. 提取内容
        content = await self._extract_content(update.message)
        
        # 3. 放入队列
        await self.queue.push({
            "message_id": update.message.message_id,
            "content": content,
            "group_id": update.message.chat_id,
            "user_id": update.message.from_user.id
        })
        
        # 4. 异步处理
        asyncio.create_task(self._process_message(content))
```

### 2.2 审核流程
```python
class ContentModeratorBase:
    async def moderate(self, content: bytes) -> ModerateResult:
        raise NotImplementedError

class ChatGPTModerator(ContentModeratorBase):
    async def moderate(self, content: bytes) -> ModerateResult:
        # 1. 预处理内容
        processed_content = await self._preprocess(content)
        
        # 2. 调用API
        result = await self._call_api(processed_content)
        
        # 3. 解析结果
        return self._parse_result(result)
```

### 2.3 回调处理流程
```python
class CallbackHandler:
    def __init__(self):
        self.registry = CallbackRegistry()
        
    @registry.register(r"^appeal:(?P<message_id>\d+)$")
    async def handle_appeal(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: str):
        # 处理申诉逻辑
        pass
        
    @registry.register(r"^mute:(?P<user_id>\d+):(?P<duration>\d+)$")
    async def handle_mute(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str, duration: str):
        # 处理禁言逻辑
        pass
```

## 3. 接口设计

### 3.1 命令接口
```python
class StartCommand(CommandBase):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 处理 /start 命令
        pass

class SettingsCommand(AdminCommand):
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # 处理 /settings 命令
        pass
```

### 3.2 自定义键盘接口
```python
class AdminKeyboard:
    @staticmethod
    def get_main_menu():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("审核设置", callback_data="settings")],
            [InlineKeyboardButton("查看日志", callback_data="logs")],
            [InlineKeyboardButton("用户管理", callback_data="users")]
        ])
    
    @staticmethod
    def get_user_actions(user_id: int):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("禁言", callback_data=f"mute:{user_id}")],
            [InlineKeyboardButton("踢出", callback_data=f"kick:{user_id}")],
            [InlineKeyboardButton("封禁", callback_data=f"ban:{user_id}")]
        ])
```

## 4. 部署方案

### 4.1 环境依赖
```
python = "^3.8"
python-telegram-bot = "^20.0"
openai = "^1.0.0"
motor = "^3.0.0"  # MongoDB异步驱动
aioredis = "^2.0.0"
pydantic = "^2.0.0"
```

### 4.2 配置文件 (config.yaml)
```yaml
bot:
  token: "YOUR_BOT_TOKEN"
  webhook_url: "https://your-domain.com/webhook"

moderator:
  type: "chatgpt"
  api_key: "YOUR_OPENAI_API_KEY"
  model: "gpt-4-vision-preview"
  temperature: 0.7

storage:
  type: "mongodb"
  uri: "mongodb://localhost:27017"
  database: "telegram_bot"

queue:
  type: "redis"
  uri: "redis://localhost:6379"
  prefix: "bot:"
```

### 4.3 监控指标
1. 性能指标
   - API响应时间
   - 队列处理延迟
   - 内存使用率
   - CPU使用率

2. 业务指标
   - 审核准确率
   - 误判率
   - 申诉成功率
   - 用户违规率
