from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.core.registry.CallbackRegistry import CallbackRegistry
from src.handlers.admin.base import AdminBaseHandler
from src.core.database.service.RuleGroupConfig import rule_group_config
from src.core.database.service.UserModerationConfigKeys import UserModerationConfigKeys as configkey

class EnableSettingHandler(AdminBaseHandler):
    """管理员审核设置处理器"""
    
    def __init__(self):
        super().__init__()
        
    def _get_rules_keyboard(self, rule_group_id: str, nsfw: bool, spam: bool, violence: bool, political: bool) -> InlineKeyboardMarkup:
        """获取规则设置键盘"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "NSFW √" if nsfw else "NSFW 检测 ❌",
                    callback_data=f"admin:rg:{rule_group_id}:moderation:rules:toggle:nsfw"
                ),
                InlineKeyboardButton(
                    "垃圾信息 √" if spam else "垃圾信息 ❌",
                    callback_data=f"admin:rg:{rule_group_id}:moderation:rules:toggle:spam"
                )
            ],
            [
                InlineKeyboardButton(
                    "暴力内容 √" if violence else "暴力内容 ❌",
                    callback_data=f"admin:rg:{rule_group_id}:moderation:rules:toggle:violence"
                ),
                InlineKeyboardButton(
                    "政治内容 √" if political else "政治内容 ❌",
                    callback_data=f"admin:rg:{rule_group_id}:moderation:rules:toggle:political"
                )
            ],
            [InlineKeyboardButton("« 返回", callback_data=f"admin:rg:{rule_group_id}:moderation:menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:moderation:rules$")
    async def handle_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则设置"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        
        # 获取当前规则状态
        rules = {
            "nsfw": await rule_group_config.get_config(rule_group_id, configkey.moderation.rules.NSFW),
            "spam": await rule_group_config.get_config(rule_group_id, configkey.moderation.rules.SPAM),
            "violence": await rule_group_config.get_config(rule_group_id, configkey.moderation.rules.VIOLENCE),
            "political": await rule_group_config.get_config(rule_group_id, configkey.moderation.rules.POLITICAL)
        }
        
        text = "⚙️ 审核规则设置\n\n"
        
        await self._safe_edit_message(
            query,
            text,
            reply_markup=self._get_rules_keyboard(rule_group_id, rules['nsfw'], rules['spam'], rules['violence'], rules['political'])
        )
        
    @CallbackRegistry.register(r"^admin:rg:.{16}:moderation:rules:toggle:(\w+)$")
    async def handle_rule_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理规则开关切换"""
        query = update.callback_query
        if not self._is_admin(query.from_user.id):
            await query.answer("⚠️ 没有权限", show_alert=True)
            return
            
        rule_group_id = query.data.split(":")[2]
        rule_type = query.data.split(":")[-1]
        
        # 获取当前状态
        current = await rule_group_config.get_config(
            rule_group_id,
            getattr(configkey.moderation.rules, rule_type.upper())
        )
        
        # 切换状态
        await rule_group_config.set_config(
            rule_group_id,
            getattr(configkey.moderation.rules, rule_type.upper()),
            not current
        )
        
        await query.answer(
            f"{'✅ 已启用' if not current else '❌ 已禁用'} {rule_type} 检测",
            show_alert=True
        )
        
        # 刷新界面
        await self.handle_rules(update, context)

    # @CallbackRegistry.register(r"^admin:settings:sensitivity$")
    # async def handle_sensitivity_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """处理敏感度设置回调"""
    #     query = update.callback_query
    #     if not self._is_admin(query.from_user.id):
    #         await query.answer("⚠️ 没有权限", show_alert=True)
    #         return

    #     text = "🎚 当前敏感度设置：\n\n"
    #     keyboard = []
        
    #     for rule, value in self.sensitivity.items():
    #         text += f"{rule.upper()}: {value:.2f}\n"
    #         keyboard.append([InlineKeyboardButton(
    #             f"调整 {rule.upper()} 敏感度",
    #             callback_data=f"admin:settings:sensitivity:adjust:{rule}"
    #         )])

    #     keyboard.append([InlineKeyboardButton("« 返回设置", callback_data="admin:settings")])
        
    #     await self._safe_edit_message(
    #         query,
    #         text,
    #         reply_markup=InlineKeyboardMarkup(keyboard)
    #     )

    # def _build_sensitivity_keyboard(self, rule: str, current_value: float) -> InlineKeyboardMarkup:
    #     """构建敏感度调整键盘"""
    #     keyboard = []
        
    #     # 添加微调按钮
    #     adjustments = [
    #         ( 0.05, "➕0.05"),
    #         (-0.05, "➖0.05"), 
    #         (-0.1 , "➖0.1" ), 
    #         ( 0.1 , "➕0.1" )
    #     ]
        
    #     # 添加调整按钮（每行两个）
    #     row = []
    #     for adj_value, label in adjustments:
    #         new_value = round(current_value + adj_value, 2)
    #         if 0 <= new_value <= 1:  # 确保值在有效范围内
    #             row.append(InlineKeyboardButton(
    #                 label,
    #                 callback_data=f"admin:settings:sensitivity:set:{rule}:{new_value}"
    #             ))
    #         if len(row) == 2:
    #             keyboard.append(row)
    #             row = []
    #     if row:  # 如果还有剩余的按钮
    #         keyboard.append(row)
        
    #     # 添加预设值按钮
    #     presets = [(0.3, "低"), (0.5, "中"), (0.7, "高"), (0.9, "严格")]
    #     row = []
    #     for value, label in presets:
    #         row.append(InlineKeyboardButton(
    #             label,
    #             callback_data=f"admin:settings:sensitivity:set:{rule}:{value}"
    #         ))
    #         if len(row) == 2:
    #             keyboard.append(row)
    #             row = []
    #     if row:
    #         keyboard.append(row)
        
    #     # 添加返回按钮
    #     keyboard.append([InlineKeyboardButton("« 返回", callback_data="admin:settings:sensitivity")])
        
    #     return InlineKeyboardMarkup(keyboard)

    # def _validate_sensitivity_value(self, value: float) -> bool:
    #     """验证敏感度值是否有效"""
    #     try:
    #         float_val = float(value)
    #         return 0 <= float_val <= 1
    #     except (ValueError, TypeError):
    #         return False

    # async def _update_sensitivity(self, rule: str, new_value: float) -> bool:
    #     """更新敏感度值"""
    #     if not self._validate_sensitivity_value(new_value):
    #         return False
            
    #     try:
    #         # 更新内存中的设置
    #         self.sensitivity[rule] = new_value
            
    #         # 保存到配置文件
    #         config_key = f"bot.settings.moderation.sensitivity.{rule}"
    #         config.set_config(config_key, new_value)
    #         return True
    #     except Exception as e:
    #         print(f"[ERROR] 更新敏感度失败: {e}")
    #         return False

    # @CallbackRegistry.register(r"^admin:settings:sensitivity:adjust:(\w+)$")
    # async def handle_sensitivity_adjust(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """处理敏感度调整"""
    #     query = update.callback_query
    #     if not self._is_admin(query.from_user.id):
    #         await query.answer("⚠️ 没有权限", show_alert=True)
    #         return

    #     rule = query.data.split(":")[4]
    #     if rule not in self.sensitivity:
    #         await query.answer("无效的规则", show_alert=True)
    #         return

    #     current_value = self.sensitivity[rule]
    #     keyboard = self._build_sensitivity_keyboard(rule, current_value)
        
    #     await self._safe_edit_message(
    #         query,
    #         f"🎚 调整 {rule.upper()} 敏感度\n"
    #         f"当前值: {current_value:.2f}\n\n"
    #         f"• 使用 ➕/➖ 按钮微调\n"
    #         f"• 或选择预设等级\n"
    #         f"（0 最宽松，1 最严格）",
    #         reply_markup=keyboard
    #     )

    # @CallbackRegistry.register(r"^admin:settings:sensitivity:set:(\w+):(\d*\.?\d*)$")
    # async def handle_sensitivity_set(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """处理敏感度设置"""
    #     query = update.callback_query
    #     if not self._is_admin(query.from_user.id):
    #         await query.answer("⚠️ 没有权限", show_alert=True)
    #         return

    #     try:
    #         rule = query.data.split(":")[-2]
    #         new_value = float(query.data.split(":")[-1])
            
    #         if rule not in self.sensitivity:
    #             await query.answer("⚠️ 无效的规则", show_alert=True)
    #             return
                
    #         if not self._validate_sensitivity_value(new_value):
    #             await query.answer("⚠️ 无效的值", show_alert=True)
    #             return
            
    #         if await self._update_sensitivity(rule, new_value):
    #             await query.answer(f"已将 {rule.upper()} 敏感度设置为 {new_value:.2f}")
    #             await self.handle_sensitivity_adjust(update, context)
    #         else:
    #             await query.answer("⚠️ 更新失败，请重试", show_alert=True)
    #     except Exception as e:
    #         print(f"[ERROR] 设置敏感度失败: {e}")
    #         await query.answer("⚠️ 发生错误，请重试", show_alert=True)

# 初始化处理器
EnableSettingHandler() 