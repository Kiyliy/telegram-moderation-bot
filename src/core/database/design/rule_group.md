# 规则组（Rule Group）设计文档

## 1. 概述
规则组是一个用于管理多个Telegram群组的逻辑单元。它允许管理员创建不同的规则组，每个规则组可以包含多个群组，并共享相同的管理规则和设置。

### 1.1 主要功能
- 管理员可以创建多个规则组
- 每个群组只能属于一个规则组
- 同一规则组内的群组共享相同的：
  - 用户警告次数
  - 违规记录
  - 封禁状态
  - 审核规则
  - 惩罚措施

## 2. 数据库设计

### 2.1 规则组表（rule_group）
```sql
CREATE TABLE rule_group (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,           -- 规则组名称
    owner_id BIGINT NOT NULL,            -- 所属管理员ID
    description TEXT,                     -- 规则组描述
    settings JSON,                        -- 规则组级别的设置
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_owner (owner_id)
);
```

settings字段JSON结构示例：
```json
{
    "warning": {
        "max_warnings": 3,           -- 最大警告次数
        "reset_after_days": 30       -- 多少天后重置警告
    },
    "punishment": {
        "mute_durations": [300, 3600, 86400],  -- 禁言时长（秒）
        "ban_threshold": 5           -- 封禁阈值
    },
    "moderation": {
        "rules": {
            "nsfw": true,            -- 是否启用NSFW检测
            "spam": true,            -- 是否启用垃圾信息检测
            "violence": false        -- 是否启用暴力内容检测
        },
        "sensitivity": {             -- 检测灵敏度
            "nsfw": 0.8,
            "spam": 0.7,
            "violence": 0.9
        }
    }
}
```

### 2.2 修改现有表结构

#### 2.2.1 群组表（chats）
```sql
ALTER TABLE chats
ADD COLUMN rule_group_id BIGINT,         -- 关联的规则组ID
ADD INDEX idx_rule_group (rule_group_id);
```

#### 2.2.2 用户警告状态表（user_warning_status）
```sql
ALTER TABLE user_warning_status
ADD COLUMN rule_group_id BIGINT NOT NULL,  -- 关联到规则组
ADD INDEX idx_rule_group_user (rule_group_id, user_id);
```

#### 2.2.3 违规记录表（user_violation）
```sql
ALTER TABLE user_violation
ADD COLUMN rule_group_id BIGINT NOT NULL,
ADD INDEX idx_rule_group (rule_group_id);
```

## 3. 服务层设计

### 3.1 规则组服务（RuleGroupService）
```python
class RuleGroupService:
    async def create_rule_group(
        self, 
        name: str, 
        owner_id: int, 
        description: str = None,
        settings: Dict = None
    ) -> Dict:
        """创建新的规则组"""
        pass
        
    async def update_rule_group(
        self, 
        group_id: int, 
        name: str = None,
        description: str = None,
        settings: Dict = None
    ) -> Dict:
        """更新规则组信息"""
        pass
        
    async def get_owner_rule_groups(
        self, 
        owner_id: int
    ) -> List[Dict]:
        """获取管理员的所有规则组"""
        pass
        
    async def get_rule_group_chats(
        self, 
        rule_group_id: int
    ) -> List[Dict]:
        """获取规则组内的所有群组"""
        pass

    async def get_rule_group_settings(
        self, 
        rule_group_id: int
    ) -> Dict:
        """获取规则组的设置"""
        pass
```

### 3.2 群组服务（ChatService）扩展
```python
class ChatService:
    async def bind_chat_to_rule_group(
        self,
        chat_id: int,
        rule_group_id: int
    ) -> Dict[str, Any]:
        """绑定群组到规则组"""
        pass

    async def unbind_chat_from_rule_group(
        self,
        chat_id: int
    ) -> Dict[str, Any]:
        """解绑群组"""
        pass
```

### 3.3 用户审核服务（UserModerationService）修改
```python
class UserModerationService:
    async def record_violation(
        self,
        rule_group_id: int,  # 改为使用rule_group_id
        user_id: int,
        chat_id: int,
        violation_type: str,
        ...
    ) -> Tuple[UserViolation, UserWarningStatus, str, Optional[int]]:
        """记录违规并更新警告状态"""
        pass

    async def get_user_status(
        self,
        rule_group_id: int,  # 改为使用rule_group_id
        user_id: int
    ) -> Optional[UserWarningStatus]:
        """获取用户在规则组中的状态"""
        pass
```

## 4. UI设计

### 4.1 管理员菜单
```
👥 群组管理
├── 📋 规则组列表
│   ├── ➕ 创建规则组
│   └── 📊 规则组详情
│       ├── ⚙️ 规则组设置
│       ├── 👥 群组列表
│       │   └── 🔗 绑定新群组
│       ├── ⚠️ 违规统计
│       └── 🚫 封禁用户
└── 🔙 返回
```

### 4.2 规则组创建流程
1. 用户点击"创建规则组"
2. 输入规则组名称
3. 输入规则组描述（可选）
4. 配置规则组设置
5. 确认创建

### 4.3 群组绑定流程
1. 在规则组详情中点击"绑定新群组"
2. 显示可绑定的群组列表（机器人所在但未绑定的群组）
3. 选择要绑定的群组
4. 确认绑定

## 5. 注意事项

### 5.1 数据迁移
- 需要为现有的群组分配默认规则组
- 需要迁移现有的警告记录和违规记录
- 需要保持现有功能的向后兼容性

### 5.2 权限控制
- 只有管理员可以创建和管理规则组
- 只有规则组的所有者可以修改规则组设置
- 群组只能被绑定到一个规则组

### 5.3 性能考虑
- 需要优化跨群组的警告和违规记录查询
- 考虑添加适当的缓存机制
- 需要注意大规模数据下的查询性能 