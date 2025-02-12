from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.MessageFilters import MessageFilters
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.chatsService import ChatService


class AdminGroupBindingHandler(AdminBaseHandler):
    """群组绑定处理器"""
    
    def __init__(self):
        super().__init__()
        self.chat_service = ChatService()

    @CallbackRegistry.register(r"^admin:groups:unbind:(-?\d+)$")
    async def handle_group_unbind(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理解除群组绑定"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        group_id = int(query.data.split(":")[-1])
        
        try:
            await self.chat_service.unbind_group_from_user(
                chat_id=group_id,
                user_id=query.from_user.id
            )
            await query.answer("✅ 解绑成功", show_alert=True)
            # 返回列表
            await query.edit_message_text(
                "👥 群组管理\n请选择要进行的操作：",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("群组列表", callback_data="admin:groups:list:1")
                ]])
            )
        except Exception as e:
            await query.answer(f"❌ 解绑失败: {str(e)}", show_alert=True)

    @MessageRegistry.register(MessageFilters.match_bot_added())
    async def handle_bot_added(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理机器人被添加到群组"""
        if not update.message or not update.message.new_chat_members:
            return
            
        # 检查是否是本机器人被添加
        bot: Bot = context.bot
        bot_id = bot.id
        
        for member in update.message.new_chat_members:
            if member.id == bot_id:
                # 机器人被添加到群组
                chat = update.message.chat
                user = update.message.from_user
                
                # 只有是supergroup才能绑定
                if chat.type != "supergroup":
                    await update.message.reply_text(
                        "⚠️ 只能在超级群组中使用本机器人\n"
                        "请将群组升级为超级群组后重试"
                    )
                    return
                    
                try:
                    # 绑定群组到用户
                    await self.chat_service.bind_group_to_user(
                        chat_id=chat.id,
                        user_id=user.id
                    )
                    
                    # 发送成功消息
                    await update.message.reply_text(
                        f"✅ 群组绑定成功\n\n"
                        f"群组: {chat.title}\n"
                        f"ID: {chat.id}\n"
                        f"类型: {chat.type}\n"
                        f"添加者: {user.full_name} ({user.id})"
                    )
                    
                    # 给用户发送私聊消息
                    try:
                        await context.bot.send_message(
                            chat_id=user.id,
                            text=f"✅ 群组 {chat.title} 绑定成功!\n"
                                 "您可以使用 /mygroups 命令管理您的群组"
                        )
                    except Exception:
                        pass  # 忽略发送私聊消息失败的情况
                        
                except Exception as e:
                    await update.message.reply_text(f"❌ 绑定失败: {str(e)}")
                break


# 初始化处理器
AdminGroupBindingHandler() 