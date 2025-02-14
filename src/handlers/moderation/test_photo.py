# src/handlers/moderation/test_photo.py
from telegram import Update
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.admin.AdminBase import AdminBaseHandler
from src.core.moderation.types.ModerationTypes import ModerationInputContent, ContentType, ModerationResult
from src.core.moderation.manager import ModerationManager
from src.core.moderation.providers.openai_moderation.openai_provider import OpenAIModerationProvider
from src.core.moderation.config import ModerationConfig
from src.core.Middleware.RuleGroupModerationConfigMiddleware import RuleGroupModerationConfigMiddleware
import traceback
from src.core.database.service.chatsService import ChatService

class TestPhotoHandler(AdminBaseHandler):
    """测试图片审核处理器"""
    
    def __init__(self):
        super().__init__()
        # 初始化审核管理器
        self.moderation_manager = RuleGroupModerationConfigMiddleware()
        self.chat_service = ChatService()
        
    async def is_manager(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        # 获取用户ID和群组ID
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
        
        # 获取用户在群组中的成员信息
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        
        # 检查用户状态
        return chat_member.status in ['administrator', 'creator', 'owner']

    @MessageRegistry.register(MessageFilters.match_media_type(['photo']))  # 直接注册图片消息处理器
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理图片消息"""
        if not self._is_admin(update.effective_user.id):
            return
            
        # 获取rule_group_id
        chat_id = update.effective_chat.id
        rule_group_id = await self.chat_service.get_chat_rule_group_id(chat_id)
        
        await update.message.reply_text("🔍 正在审核图片...")
        
        # 获取是否是管理员
        is_manager = await self.is_manager(update, context)
        
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
            result: ModerationResult = await self.moderation_manager.check_content(
                rule_group_id=rule_group_id, 
                content=input_data, 
                is_manager=is_manager
                )
            print(result)
            
            # 格式化结果
            text = "📋 审核结果:\n\n"
            text += f"是否违规: {'✅ 是' if result.flagged else '❌ 否'}\n\n"
            # if result.flagged:
            if True:
                text += "类别:\n"
                for category, is_flagged in result.categories.items():
                    score = result.category_scores[category]  # 用 key 来确保对应关系
                    text += f"- {category}: {score:.2%}\n"
                        
            # 反馈给用户
            await update.message.reply_text(text)
            
            # 如果违规, 删除用户的消息
            if result.flagged:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
            
        except Exception as e:
            print(f"❌ 审核失败: {str(e)}, {traceback.format_exc()}")
            await update.message.reply_text(f"❌ 审核失败: {str(e)}")

    @MessageRegistry.register(MessageFilters.match_media_type(['video']))  # 直接注册图片消息处理器
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理视频消息"""
        if not self._is_admin(update.effective_user.id):
            return
            
        await update.message.reply_text("🔍 正在审核视频...")
                    
        # 获取rule_group_id
        chat_id = update.effective_chat.id
        rule_group_id = await self.chat_service.get_chat_rule_group_id(chat_id)
        
        # 获取是否是管理员
        is_manager = await self.is_manager(update, context)
        
        try:
            video = update.message.video
            file = await context.bot.get_file(video.file_id)
            
            # 创建审核输入
            input_data = ModerationInputContent(
                type=ContentType.VIDEO,
                video=file.file_path
            )
            
            # 执行审核
            result: ModerationResult = await self.moderation_manager.check_content(
                rule_group_id=rule_group_id, 
                content=input_data, 
                is_manager=is_manager
                )
            
            # 格式化结果
            text = "📋 审核结果:\n\n"
            text += f"是否违规: {'✅ 是' if result.flagged else '❌ 否'}\n\n"
            
            if result.flagged:
                text += "违规类别:\n"
                for (cat, is_flagged), score in zip(result.categories.items(), 
                                                result.category_scores.values()):
                    if is_flagged:
                        text += f"- {cat}: {score:.2%}\n"
                        
            await update.message.reply_text(text)
            
        except Exception as e:
            print(f"❌ 审核失败: {str(e)}, {traceback.format_exc()}")
            await update.message.reply_text(f"❌ 审核失败: {str(e)}")

# 初始化处理器
TestPhotoHandler()