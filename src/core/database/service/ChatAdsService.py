from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from src.core.config.config import config
from src.core.database.service.chatsService import ChatService
import random
import traceback
from src.core.logger import logger


class ChatAdsService:

    def __init__(self):
        self.chat_service = ChatService()
        self.config = config()

    def _format_ad_text_markdowns(self, ad_text_markdowns):
        """
        兼容多种ad_text_markdowns的格式, 返回一个ad_text_markdowns
        比如:
        1. {"ad1": 10, "ad2": 20}
        根据权重随机返回ad1或2
        2. ["ad1", "ad2]
        随机返回ad1或ad2
        3. "ad1"
        直接返回ad1
        4. null
        返回空字符串
        同时兼容:
        {
            "ad_text_markdowns":
        }
        这种config文件未处理的格式
        """

        def _get_ad_text_from_dict(ad_text_markdowns):
            ads = list(ad_text_markdowns.keys())
            weights = list(ad_text_markdowns.values())

            # 根据权重随机选择一条广告
            selected_ad = random.choices(ads, weights=weights, k=1)[0]
            return selected_ad

        def _get_ad_text_from_list(ad_text_markdowns):
            return random.choice(ad_text_markdowns)

        ad_text_markdowns = ad_text_markdowns
        # 先兼容config文件未处理的格式
        if isinstance(ad_text_markdowns, dict):
            ad_text_markdowns = (
                ad_text_markdowns.get("ad_text_markdowns") or ad_text_markdowns
            )

        # 再根据类型返回
        if isinstance(ad_text_markdowns, dict):
            return _get_ad_text_from_dict(ad_text_markdowns)
        elif isinstance(ad_text_markdowns, list):
            return _get_ad_text_from_list(ad_text_markdowns)
        elif ad_text_markdowns is None:
            return ""
        elif isinstance(ad_text_markdowns, str):
            return ad_text_markdowns
        # 如果还有其它情况
        else:
            return str(ad_text_markdowns)

    def _format_buttons_layout(self, buttons_layout):
        """
        兼容多种buttons_layout的格式, 返回一个buttons_layout
        [[]]
        直接返回:
        或者
        [[[1]],[[2]],[[3]]]
        或者
        {
            "buttons1": [[1]],
            "buttons2": [[2]],
            "buttons3": [[3]]
        }
        同时兼容config文件未处理的格式
        {
            "buttons": xxx
        }
        """

        def _get_buttons_layout_from_dict(buttons_layout):
            button_data = []
            weights = []
            # 如果是根据权重随机选择的buttons, 则根据权重随机选择一条
            for button_key, button in buttons_layout.items():
                button_data.append(button.get("buttons", []))
                weights.append(button.get("weight", 1))

            # 根据权重随机选择一条广告
            selected_button = random.choices(button_data, weights=weights, k=1)[0]
            return selected_button

        def _get_buttons_layout_from_list(buttons_layout):
            """
            处理按钮布局列表，支持三种格式：
            0. 无按钮 [[]]
            1. 单个按钮布局：[[{}]]
            直接返回
            2. 多个可选按钮布局：[[[button1]], [[button2]], [[button3]]]
            随机返回一条
            """
            # 如果是[[]], len(list[0]) == 0
            if len(buttons_layout[0]) == 0:
                return [[]]

            # 通过检查第一个元素的嵌套深度来判断布局类型
            is_single_layout = isinstance(
                buttons_layout[0][0], dict
            )  # button配置是dict类型

            # 如果是单个按钮布局, 直接返回
            if is_single_layout:
                return buttons_layout
            # 如果是多个按钮布局的list, 根据随机选择一条
            else:
                return random.choice(buttons_layout)

        buttons_layout = buttons_layout
        # 兼容config文件未处理的格式
        if isinstance(buttons_layout, dict):
            buttons_layout = buttons_layout.get("buttons") or buttons_layout

        # 再根据类型返回
        if isinstance(buttons_layout, list):
            return _get_buttons_layout_from_list(buttons_layout)
        elif isinstance(buttons_layout, dict):
            return _get_buttons_layout_from_dict(buttons_layout)
        else:
            return buttons_layout

    @classmethod
    def _create_markup_from_buttons_layout(cls, buttons_layout):
        """
        创建按钮布局, 如果没有按钮, 返回None
        : 示例按钮布局
        InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=f"🤖 点击获取答案",
                        callback_data="gpt:"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "我也要玩", switch_inline_query_current_chat=""
                    )
                ],
            ]
        )
        """
        try:
            # 提取按钮布局
            # buttons_layout = layout_dict.get("buttons", [])

            # 如果没有按钮, 返回None
            if not buttons_layout or buttons_layout == [[]]:
                return None

            buttons_markup = []
            # 遍历每一行的按钮配置
            for row in buttons_layout:
                buttons = []
                for button in row:
                    # 根据 button 的配置创建 InlineKeyboardButton 对象
                    if "callback_data" in button:
                        buttons.append(
                            InlineKeyboardButton(
                                text=button["text"],
                                callback_data=button["callback_data"],
                            )
                        )
                    elif "url" in button:
                        buttons.append(
                            InlineKeyboardButton(text=button["text"], url=button["url"])
                        )
                    elif "switch_inline_query_current_chat" in button:
                        buttons.append(
                            InlineKeyboardButton(
                                text=button["text"],
                                switch_inline_query_current_chat=button[
                                    "switch_inline_query_current_chat"
                                ],
                            )
                        )
                    elif "switch_inline_query" in button:
                        buttons.append(
                            InlineKeyboardButton(
                                text=button["text"],
                                switch_inline_query=button["switch_inline_query"],
                            )
                        )
                buttons_markup.append(buttons)

            # 创建 InlineKeyboardMarkup 对象
            markup = InlineKeyboardMarkup(buttons_markup)

            return markup
        except Exception:
            logger.error("创建按钮布局失败!", exc_info=True)
            print(f"创建按钮布局失败!{traceback.format_exc()}")
            return None

    async def get_chat_buttons_markup(self, chat_id: int):
        """
        根据chat_id获取一个buttons_markup
        """
        buttons_config = None
        default_buttons_config = self.config.get_messageCaption_buttons()
        override_buttons_config = (
            self.config.get_override_group_buttons()
            if chat_id < 0
            else self.config.get_override_private_buttons()
        )

        try:
            # 根据优先级 chat_info.ads > override > default
            # 如果ads==None -> 说明获取失败, 默认为空button
            # 如果ads.buttons为str(default), 则使用default的buttons, 而绕过override的覆盖
            # 如果ads.buttons为dict, 则使用ads.buttons, 否则使用配置文件的buttons
            ads = await self.chat_service._get_chats_ads(chat_id)
            if ads == None:
                buttons_config = [[]]
            elif ads.get("buttons", {}) == "default":
                buttons_config = default_buttons_config
            elif ads.get("buttons"):
                buttons_config = ads.get("buttons")
            else:
                # 如果ads没有buttons, 使用配置文件的buttons, override > default
                buttons_config = override_buttons_config or default_buttons_config

            # 取出一个buttons_markup并格式化为buttons对象
            buttons_markup = self._format_buttons_layout(buttons_config)
            return self._create_markup_from_buttons_layout(buttons_markup)
        except Exception:
            logger.error("获取chat buttons失败!", exc_info=True)
            print(f"获取chat buttons失败!{traceback.format_exc()}")
            return None

    async def get_chat_ads_text(self, chat_id: int) -> str:
        """
        获取chat的ads的ad_text_markdowns
        """
        ad_text_config = None
        default_ad_text_markdowns = self.config.get_messageCaption_ad_text_markdown()
        override_ad_text_markdowns = (
            self.config.get_override_group_text_markdowns()
            if chat_id < 0
            else self.config.get_override_private_text_markdowns()
        )

        try:
            # 获取chat_info.ads
            ads = await self.chat_service._get_chats_ads(chat_id)
            # 如果chat_info.ads的ad_text_markdowns, 为str(default), 则使用default的ad_text_markdowns
            # 如果chat_info.ads的ad_text_markdowns存在, 则使用chat_info.ads
            # 否则使用配置文件的ad_text_markdowns, override > default
            if ads is None:  # 如果ads==None, 说明获取失败了 -> 默认为空
                ad_text_config = {"ad_text_markdowns": " "}
            elif ads.get("ad_text_markdowns") == "default":
                ad_text_config = default_ad_text_markdowns
            elif ads.get("ad_text_markdowns"):
                ad_text_config = ads.get("ad_text_markdowns", "")
            else:
                ad_text_config = override_ad_text_markdowns or default_ad_text_markdowns
            return self._format_ad_text_markdowns(ad_text_config)
        except Exception:
            logger.error("获取chat ads失败!", exc_info=True)
            print(f"获取chat ads失败!{traceback.format_exc()}")
            return ""
