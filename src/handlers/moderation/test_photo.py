from telegram import Update
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from src.core.moderation.models import ModerationInput, ContentType
from src.core.moderation.manager import ModerationManager
from src.core.moderation.providers.openai_provider import OpenAIModerationProvider
from src.core.moderation.config import ModerationConfig

class TestPhotoHandler(AdminBaseHandler):
    """测试图片审核处理器"""
    
    def __init__(self):
        super().__init__()
        # 初始化审核管理器
        self.moderation_manager = ModerationManager([
            OpenAIModerationProvider(
                api_key=ModerationConfig.OPENAI_API_KEY,
                model=ModerationConfig.OPENAI_MODERATION_MODEL
            )
        ])

    @CallbackRegistry.register(r"^test:photo$")
    async def handle_test_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理测试图片审核"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        await query.message.reply_text(
            "请发送要测试的图片或视频"
        )
        # 设置下一步处理器
        context.user_data["next_handler"] = self.process_media
        
    async def process_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理媒体文件"""
        if not update.message or (not update.message.photo and not update.message.video):
            await update.message.reply_text("❌ 请发送图片或视频")
            return
            
        await update.message.reply_text("🔍 正在审核内容...")
        
        try:
            if update.message.photo:
                # 获取最大尺寸的图片
                photo = update.message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                
                # 创建审核输入
                input_data = ModerationInput(
                    type=ContentType.IMAGE,
                    content=file.file_path
                )
                
            elif update.message.video:
                video = update.message.video
                file = await context.bot.get_file(video.file_id)
                
                # 创建审核输入
                input_data = ModerationInput(
                    type=ContentType.VIDEO,
                    content=file.file_path
                )
            
            # 执行审核
            result = await self.moderation_manager.check_content(input_data)
            
            # 格式化结果
            text = "📋 审核结果:\n\n"
            text += f"是否违规: {'✅ 是' if result.flagged else '❌ 否'}\n\n"
            
            if result.flagged:
                text += "违规类别:\n"
                for category, detail in result.categories.items():
                    if detail.flagged:
                        text += f"- {category}: {detail.score:.2%}\n"
                        
            await update.message.reply_text(text)
            
        except Exception as e:
            await update.message.reply_text(f"❌ 审核失败: {str(e)}")
        finally:
            # 清除处理器
            context.user_data.pop("next_handler", None)

# 初始化处理器
TestPhotoHandler() 