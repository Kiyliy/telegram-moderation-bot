# src/handlers/moderation/test_photo.py
from telegram import Update
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.MessageFilters import MessageFilters
from handlers.admin.AdminBase import AdminBaseHandler
from src.core.moderation.types.ModerationTypes import ModerationInputContent, ContentType
from src.core.moderation.manager import ModerationManager
from src.core.moderation.providers.openai_moderation.openai_provider import OpenAIModerationProvider
from src.core.moderation.config import ModerationConfig
import traceback

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

    # @MessageRegistry.register(MessageFilters.match_media_type(['photo','video']))  # 直接注册图片消息处理器
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理图片消息"""
        if not self._is_admin(update.effective_user.id):
            return
            
        await update.message.reply_text("🔍 正在审核图片...")
        
        try:
            # 获取最大尺寸的图片
            if update.message.photo:
                photo = update.message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
            elif update.message.video:
                video = update.message.video
                file = await context.bot.get_file(video.file_id)
            
            # 创建审核输入
            input_data = ModerationInputContent(
                type=ContentType.IMAGE_URL,
                image_urls=[file.file_path]
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
            print(f"❌ 审核失败: {str(e)}, {traceback.format_exc()}")
            await update.message.reply_text(f"❌ 审核失败: {str(e)}")

    @MessageRegistry.register(MessageFilters.match_media_type(['video']))  # 直接注册图片消息处理器
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理视频消息"""
        if not self._is_admin(update.effective_user.id):
            return
            
        await update.message.reply_text("🔍 正在审核视频...")
        
        try:
            video = update.message.video
            file = await context.bot.get_file(video.file_id)
            
            # 创建审核输入
            input_data = ModerationInputContent(
                type=ContentType.VIDEO,
                video=file.file_path
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
            print(f"❌ 审核失败: {str(e)}, {traceback.format_exc()}")
            await update.message.reply_text(f"❌ 审核失败: {str(e)}")

# 初始化处理器
TestPhotoHandler()