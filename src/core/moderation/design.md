

首先,我们需要创建设计文档:

```markdown
# Moderation 审核模块设计文档

## 1. 模块目标
- 提供统一的内容审核接口
- 支持多种审核服务提供商(OpenAI, GPT-4等)
- 支持文本和图片的审核
- 提供可扩展的审核结果处理机制

## 2. 核心接口设计

### 2.1 基础接口
```python
class IModerationProvider:
    """审核服务提供者接口"""
    async def check_text(self, text: str) -> ModerationResult:
        """文本审核"""
        pass
        
    async def check_image(self, image_url: str) -> ModerationResult:
        """图片审核"""
        pass
        
    async def check_mixed(self, content: List[ModerationInput]) -> ModerationResult:
        """混合内容审核"""
        pass
```

### 2.2 数据模型
```python
class ModerationInput:
    """审核输入"""
    type: str  # "text" or "image_url"
    content: str  # 文本内容或图片URL
    
class ModerationResult:
    """审核结果"""
    flagged: bool  # 是否违规
    categories: Dict[str, bool]  # 各个类别的违规标记
    category_scores: Dict[str, float]  # 各个类别的违规分数
    provider: str  # 提供者标识
    raw_response: Dict  # 原始响应
```

## 3. 具体实现

### 3.1 OpenAI Moderation
```python
class OpenAIModerationProvider(IModerationProvider):
    """OpenAI审核服务提供者"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def check_text(self, text: str) -> ModerationResult:
        # 实现OpenAI文本审核
        pass
```

### 3.2 GPT-4 Moderation
```python
class GPT4ModerationProvider(IModerationProvider):
    """GPT-4审核服务提供者"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def check_text(self, text: str) -> ModerationResult:
        # 实现GPT-4文本审核
        pass
```


## 5. 审核管理器

```python
class ModerationManager:
    """审核管理器"""
    def __init__(
        self,
        providers: List[IModerationProvider],
        cache: Optional[IModerationCache] = None
    ):
        self.providers = providers
        self.cache = cache
        
    async def check_content(
        self,
        content: Union[str, List[ModerationInput]],
        provider_name: Optional[str] = None
    ) -> ModerationResult:
        # 实现内容审核逻辑
        pass
```
{
    "raw_response": dict,  # 原始完整响应
    "content": str,       # 原始内容
    "flagged": bool,      # 是否违规
    "categories": dict,   # 违规类别
    "scores": dict       # 各类别的分数
}

## 6. 使用示例

```python
# 初始化
moderation_manager = ModerationManager([
    OpenAIModerationProvider(api_key="..."),
    GPT4ModerationProvider(api_key="...")
], cache=RedisModerationCache())

# 使用
result = await moderation_manager.check_content("要审核的内容")
if result.flagged:
    print("内容违规")
    print("违规类别:", result.categories)
```

## 7. 扩展性考虑

1. 新增审核提供者:
   - 实现 `IModerationProvider` 接口
   - 在配置中添加新提供者

2. 自定义缓存:
   - 实现 `IModerationCache` 接口
   - 替换默认的Redis缓存

3. 结果处理:
   - 可以通过继承 `ModerationResult` 扩展结果处理逻辑
   - 支持自定义违规类别和分数计算

## 8. 配置项




demo:
# 使用示例
async def main():
    # 初始化管理器
    manager = ModerationManager([
        OpenAIModerationProvider(api_key="your-api-key")
    ])
    
    # 检查单张图片
    result = await manager.check_content(ModerationInput(
        type=ContentType.IMAGE,
        content="https://example.com/image.jpg"
    ))
    
    # 检查多张图片
    result = await manager.check_content(ModerationInput(
        type=ContentType.IMAGE,
        content=[
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg"
        ]
    ))
    
    # 检查视频
    result = await manager.check_content(ModerationInput(
        type=ContentType.VIDEO,
        content="https://example.com/video.mp4"
    ))
    
    # 处理结果
    if result.flagged:
        print("内容违规!")
        for category, detail in result.categories.items():
            if detail.flagged:
                print(f"违规类型: {category}, 置信度: {detail.score}")