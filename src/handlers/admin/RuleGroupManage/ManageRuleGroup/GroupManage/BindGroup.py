from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.core.registry.MessageRegistry import MessageRegistry
from src.core.registry.MessageFilters import MessageFilters
from handlers.admin.AdminBase import AdminBaseHandler
from src.core.database.service.chatsService import ChatService
import asyncio
from src.core.database.models.db_chat import ChatInfo
from typing import List
class AdminGroupBindingHandler(AdminBaseHandler):
    """群组绑定处理器"""
    
    def __init__(self):
        super().__init__()
        self.chat_service = ChatService()

    @CallbackRegistry.register(r"^admin:rg:.{16}:groups:unbind:(-?\d+)$")
    async def handle_group_unbind(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        将群组从规则组中移除
        
        1. 检查是否是管理员
        2. 检查群组是否属于规则组
        3. 移除群组绑定
        4. 返回列表
        """
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        group_id = int(query.data.split(":")[-1])
        rule_group_id = query.data.split(":")[2]
        
        try:
            await self.chat_service.unbind_chat_from_rule_group(
                chat_id=group_id
            )
            await query.answer("✅ 解绑成功", show_alert=True)
            # 返回列表
            await query.edit_message_text(
                "👥 群组管理\n请选择要进行的操作：",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("👥 群组列表", callback_data=f"admin:rg:{rule_group_id}:groups:list:1")
                ]])
            )
        except Exception as e:
            await query.answer(f"❌ 解绑失败: {str(e)}", show_alert=True)

    @MessageRegistry.register(MessageFilters.match_bot_added())
    async def handle_bot_added(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理机器人被添加到群组, 将群组绑定到用户
        
        1. 检查是否是本机器人被添加
        2. 检查是否是超级群组
        3. 绑定群组到用户
        4. 发送成功消息
        5. 发送私聊消息
        """
        if not update.message or not update.message.new_chat_members:
            return
        # 检查是否是本机器人被添加
        bot: Bot = context.bot
        bot_id = bot.id
        print(update)
        for member in update.message.new_chat_members:
            if member.id == bot_id:
                # 机器人被添加到群组
                chat = update.message.chat
                user = update.message.from_user
                
                # 只有是supergroup才能绑定
                if chat.type != "supergroup" and chat.api_kwargs.get('all_members_are_administrators', True) == False:
                    await update.message.reply_text(
                        "⚠️ 只能在超级群组中使用本机器人\n"
                        "请将群组升级为超级群组后重试"
                    )
                    return
                    
                try:
                    # 绑定群组到用户, 等待1秒, 时序问题
                    # 此时群组的info, 还没有完全插入到, 数据库中
                    await asyncio.sleep(1)
                    await self.chat_service.bind_group_to_user(
                        group_id=chat.id,
                        user_id=user.id
                    )
                    
                    # 发送成功消息
                    await update.message.reply_text(
                        f"✅ 机器人已成功加入群组\n\n"
                        f"群组: {chat.title}\n"
                        f"ID: {chat.id}\n"
                        f"类型: {chat.type}\n"
                        f"添加者: {user.full_name} ({user.id})\n\n"
                        f"请使用 /mygroups 命令将群组绑定到规则组"
                    )
                    
                    # 给用户发送私聊消息
                    try:
                        await context.bot.send_message(
                            chat_id=user.id,
                            text=f"✅ 机器人已成功加入群组 {chat.title}!\n"
                                 "请使用 /mygroups 命令将群组绑定到规则组"
                        )
                    except Exception:
                        pass  # 忽略发送私聊消息失败的情况
                        
                except Exception as e:
                    await update.message.reply_text(f"❌ 绑定失败: {str(e)}")
                break
    
    @CallbackRegistry.register(r"^admin:rg:.{16}:groups:bind_existing(:menu)?$")
    async def handle_show_bind_existing_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        显示群组绑定菜单
        1. 检查是否是管理员
        2. 列举所有未绑定的群组
        3. 点击可以进行绑定
        
        """
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
        
        rule_group_id = query.data.split(":")[2]
        
        unbind_group_list: List[ChatInfo] = await self.chat_service.get_unbound_chats(user_id=query.from_user.id)
            
        # 将未绑定的群组, 添加到键盘
        keyboard = []
        if unbind_group_list:
            for group in unbind_group_list:
                keyboard.append([InlineKeyboardButton(f"🔄 {group.title}", callback_data=f"admin:rg:{rule_group_id}:groups:bind:{group.chat_id}")])
        reply_text = "👥 群组管理\n以下是您未绑定的群组, 点击群组将其进行绑定："
        if not unbind_group_list:
            reply_text = "👥 群组管理\n当前没有未绑定的群组\n请选择要进行的操作："
        
        # 修复这里的键盘布局
        keyboard.append(
            [
                InlineKeyboardButton("🔄 刷新页面", callback_data=f"admin:rg:{rule_group_id}:groups:bind_existing"),
                InlineKeyboardButton("« 返回列表", callback_data=f"admin:rg:{rule_group_id}:groups:list:1")
            ]
        )
        
        await query.edit_message_text(
            reply_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:groups:bind:(-?\d+)$")
    async def handle_group_bind(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        """
        将群组绑定到规则组
        1. 检查是否是管理员
        2. 绑定群组到规则组
        3. 返回列表
        """
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
        
        chat_id = int(query.data.split(":")[-1])
        rule_group_id = query.data.split(":")[2]
        
        await self.chat_service.bind_chat_to_rule_group(
            chat_id=chat_id,
            rule_group_id=rule_group_id
        )
        
        await query.answer("✅ 绑定成功", show_alert=True)
        await query.edit_message_text(
            "👥 群组管理\n请选择要进行的操作：",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("👥 群组列表", callback_data=f"admin:rg:{rule_group_id}:groups:list:1")
            ]])
        )
        
# 初始化处理器
AdminGroupBindingHandler() 