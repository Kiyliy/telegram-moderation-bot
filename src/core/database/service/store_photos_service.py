from telegram import Update
from telegram.ext import CallbackContext
import asyncio
from src.core.logger import logger
import traceback
from src.core.database.service.messageHistoryService import MessageHistoryService
import time


class store_photos_service:
    msg_history_service = MessageHistoryService()
    # 用于临时存储照片组的字典
    photo_groups = {}

    # 设置一个较短的超时时间（例如 0.5 秒）
    TIMEOUT = 1.5

    async def store_user_message_with_photos(
        self, update: Update, context: CallbackContext, message_text: str = None
    ):
        message = update.message
        user_id = message.from_user.id
        chat_id = message.chat_id
        message_id = message.message_id
        try:
            if not message.media_group_id:
                # 如果没有图片或者只有一张图片
                if message.photo:
                    # 获取图片id, 获取图片url
                    photo_id = update.message.photo[-1].file_id
                    photo = await context.bot.get_file(photo_id)
                    photo_url = photo.file_path
                photo_url_list = [photo_url] if message.photo else None

                await self.msg_history_service._store_message(
                    chat_id=chat_id,
                    message_id=message_id,
                    user_id=user_id,
                    from_type="bot" if message.from_user.is_bot else "user",
                    message_text=(
                        message_text
                        if message_text
                        else (message.text or message.caption)
                    ),
                    photo_url_list=photo_url_list,
                    reply_to_message_id=(
                        message.reply_to_message.id
                        if message.reply_to_message
                        else None
                    ),
                )
            else:
                # 如果是照片组的一部分
                if user_id not in self.photo_groups:
                    self.photo_groups[user_id] = {}

                # 如果是照片组的第一张图片, 则创建一个新的字典
                is_first_photo = (
                    message.media_group_id not in self.photo_groups[user_id]
                )

                if is_first_photo:
                    self.photo_groups[user_id][message.media_group_id] = {
                        "photos": [],
                        "text": message.caption,
                        "message_id": message_id,
                        "start_time": asyncio.get_event_loop().time(),
                        "last_update_time": asyncio.get_event_loop().time(),
                        "processed": False,
                        "reply_to_message_id": (
                            message.reply_to_message.id
                            if message.reply_to_message
                            else None
                        ),
                        "processing_complete": asyncio.Event(),
                        "processing_task": None,
                    }

                # 将照片添加到照片组的字典中
                group_info = self.photo_groups[user_id][
                    message.media_group_id
                ]  # -> 这里是一个引用
                # 获取图片id, 获取图片url
                photo_id = update.message.photo[-1].file_id
                photo = await context.bot.get_file(photo_id)
                photo_url = photo.file_path
                # 如果不是第一张图片, 则将照片添加到照片组的末尾, 如果是第一张图片, 则将照片添加到照片组的开头
                (
                    group_info["photos"].append(photo_url)
                    if not is_first_photo
                    else group_info["photos"].insert(0, photo_url)
                )
                group_info["last_update_time"] = asyncio.get_event_loop().time()

                # 异步会创建单独的变量, 所以没有办法使用变量的方式去处理
                # 如果只是is_first_photo就处理的话, 无法刷新时间, 图片比较多的时候就会漏掉图片这样
                # if is_first_photo:
                #     # 对于第一张图片，我们立即开始处理
                #     photo_progress = await self.delayed_process_photo_group(user_id, message.media_group_id, chat_id, message_id)
                # else:
                #     photo_progress.cancel()
                #     photo_progress = await self.delayed_process_photo_group(user_id, message.media_group_id, chat_id, message_id)
                # 取消之前的处理任务（如果存在）

                # 如果是第一张图片 -> 创建新的处理任务
                # 如果是后续的图片 -> 将旧的处理任务取消, 创建新的处理任务 -> 刷新时间
                # 因为group_info['processing_task']已经是强引用, 所以不用担心被垃圾回收掉

                # debug
                print(f"收到图片{message.media_group_id}的时间为: {time.time()}")

                # 等待这个新的任务
                # 这里有个bug, 因为是处于异步的状态中, 我存的msg_id是根据第一张图片来存的, 找history的时候也是根据第一张图片来存的
                # 但是第一张图片的异步过程中, 这个group_info['processing_task'] 被第二张图片取消了, 于是第一张图片就返回了, 然后就直接开始处理AI了
                # 我一开始也是这样写的, 但是后来改成硬延迟, 就是因为这个原因(硬延迟就是第一张图片在等待)
                # 但是硬延迟又会出现新的问题, 就是如果图片很多的话, 那么等待的时间就会很长, 这就会导致msg_id和history的msg_id不匹配
                # 所以需要优化这里, 1. 延迟要处于第一张图片上来, 2. 不要设置硬延迟

                # 解决方案
                # 第一张图片的环节中, 如果有group_info['processing_task']则等待
                # 这个时候会遇到任务被取消的情况, 那么就重新读取任务, 然后重新等待, 直到这个任务被完成

                # 这个解决方案有一个bug, 因为设计的是依赖于第一个图片的异步进程, 那么所有的参数等都必须使用第一个图片的, 取消任务过后重新读取任务
                # 这个delayed_process_photo_group函数的参数就变成最后一张图片的了, 就导致引用的时候检索不到msg

                # 最后的解决方案
                # 如果是第一张图片, 则创建新的处理任务, 然后等待这个任务的完成
                # 这个等待任务的完成采用group_info['processing_complete'].wait()去实现
                # 但是还是不能刷新时间, 还是要用其它图片去取消

                # 取消之前的处理任务（如果存在）, 然后创建新的任务
                if group_info["processing_task"]:
                    group_info["processing_task"].cancel()

                group_info["processing_task"] = asyncio.create_task(
                    self.delayed_process_photo_group(
                        user_id, message.media_group_id, chat_id
                    )
                )

                if is_first_photo:
                    # 第一张图片会持续等待任务的完成, 知道最后一张图片超时, 然后执行逻辑, 将这个event设置为set
                    await group_info["processing_complete"].wait()
                    print(f"第一张图片处理结束时间为{time.time()}")

        except Exception:
            logger.error(f"保存user messages时出现错误!: {traceback.format_exc()}")
            print(f"保存user messages时出现错误!: {traceback.format_exc()}")

    async def delayed_process_photo_group(
        self, user_id: int, media_group_id: str, chat_id: int
    ):
        try:
            await asyncio.sleep(self.TIMEOUT)
            await self.process_photo_group(user_id, media_group_id, chat_id)
        except asyncio.CancelledError:
            pass

    async def process_photo_group(
        self, user_id: int, media_group_id: str, chat_id: int
    ):
        try:
            if (
                user_id in self.photo_groups
                and media_group_id in self.photo_groups[user_id]
            ):
                group_info = self.photo_groups[user_id][media_group_id]

                if group_info["processed"]:
                    return

                group_info["processed"] = True
                photos = group_info["photos"]
                text = group_info["text"]
                reply_to_message_id = group_info["reply_to_message_id"]
                message_id = group_info["message_id"]

                await self.msg_history_service._store_message(
                    chat_id=chat_id,
                    user_id=user_id,
                    message_id=message_id,
                    from_type="user",
                    message_text=text,
                    photo_url_list=photos,
                    reply_to_message_id=reply_to_message_id,  # 假设照片组没有回复其他消息
                )

                # 处理完毕后，删除临时存储的照片组
                del self.photo_groups[user_id][media_group_id]
                if not self.photo_groups[user_id]:
                    del self.photo_groups[user_id]

                print(f"处理图片组{media_group_id}的时间为: {time.time()}")
                group_info["processing_complete"].set()

        except Exception:
            logger.error(f"process photo group时出现错误!{traceback.format_exc()}")
            print(f"process photo group时出现错误!{traceback.format_exc()}")
