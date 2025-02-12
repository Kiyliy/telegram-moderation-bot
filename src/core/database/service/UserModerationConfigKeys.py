from enum import Enum

class UserModerationConfigKeys:
    """用户管理配置键"""
    class moderation:
        """审核规则配置"""
        class rules:
            """规则开关"""
            NSFW: str = 'moderation.rules.nsfw'
            VIOLENCE: str = 'moderation.rules.violence'
            POLITICAL: str = 'moderation.rules.political'
            SPAM: str = 'moderation.rules.spam'
        
        class sensitivity:
            """规则灵敏度"""
            NSFW: str = 'moderation.sensitivity.nsfw'
            VIOLENCE: str = 'moderation.sensitivity.violence'
            POLITICAL: str = 'moderation.sensitivity.political'
            SPAM: str = 'moderation.sensitivity.spam'
        
        class auto_actions:
            """自动处理动作"""
            DELETE_MESSAGE: str = 'moderation.auto_actions.delete_message'
            WARN_USER: str = 'moderation.auto_actions.warn_user'
            NOTIFY_ADMINS: str = 'moderation.auto_actions.notify_admins'
    
    class warning_messages:
        """警告消息配置"""
        NSFW: str = 'warning_messages.nsfw'
        VIOLENCE: str = 'warning_messages.violence'
        POLITICAL: str = 'warning_messages.political'
        SPAM: str = 'warning_messages.spam'
    
    class punishment:
        """惩罚措施配置"""
        MUTE_DURATIONS: str = 'punishment.mute_durations'
        BAN_THRESHOLD: str = 'punishment.ban_threshold'
        WARNING_RESET_DAYS: str = 'punishment.warning_reset_days'
        MAX_WARNINGS: str = 'punishment.max_warnings' 