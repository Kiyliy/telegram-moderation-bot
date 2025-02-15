from enum import Enum

class UserModerationConfigKeys:
    """用户管理配置键"""
    class moderation:
        """审核规则配置"""

        PROVIDER_LIST: str = 'moderation.provider_list'
        ACTIVE_PROVIDER: str = 'moderation.active_provider'
        
        # 其他配置
        OTHER_CONFIG: str = 'moderation.other_config'
        class other_config:
            SKIP_MANAGER: str = 'moderation.other_config.skip_manager'

        # 自动处理动作
        AUTO_ACTIONS: str = 'moderation.auto_actions'
        class auto_actions:
            """自动处理动作"""
            DELETE_MESSAGE: str = 'moderation.auto_actions.delete_message'
            WARN_USER: str = 'moderation.auto_actions.warn_user'
            NOTIFY_ADMINS: str = 'moderation.auto_actions.notify_admins'
    
        PROVIDERS: str = 'moderation.providers'
        class providers:
            """审核提供者"""
            OPENAI: str = 'moderation.providers.openai'
            class openai:
                CATEGORIES: str = 'moderation.providers.openai.categories'
                SENSITIVITY: str = 'moderation.providers.openai.sensitivity'
                class categories:
                    SEXUAL_MINORS = "moderation.providers.openai.categories.sexual/minors"
                    HARASSMENT = "moderation.providers.openai.categories.harassment"
                    HARASSMENT_THREATENING = "moderation.providers.openai.categories.harassment/threatening"
                    HATE = "moderation.providers.openai.categories.hate"
                    HATE_THREATENING = "moderation.providers.openai.categories.hate/threatening"
                    ILLICIT = "moderation.providers.openai.categories.illicit"
                    ILLICIT_VIOLENT = "moderation.providers.openai.categories.illicit/violent"
                    SELF_HARM = "moderation.providers.openai.categories.self-harm"
                    SELF_HARM_INTENT = "moderation.providers.openai.categories.self-harm/intent"
                    SELF_HARM_INSTRUCTIONS = "moderation.providers.openai.categories.self-harm/instructions"
                    VIOLENCE = "moderation.providers.openai.categories.violence"
                    VIOLENCE_GRAPHIC = "moderation.providers.openai.categories.violence/graphic"
                class sensitivity:
                    SEXUAL_MINORS = "moderation.providers.openai.sensitivity.sexual/minors"
                    HARASSMENT = "moderation.providers.openai.sensitivity.harassment"
                    HARASSMENT_THREATENING = "moderation.providers.openai.sensitivity.harassment/threatening"
                    HATE = "moderation.providers.openai.sensitivity.hate"
                    HATE_THREATENING = "moderation.providers.openai.sensitivity.hate/threatening"
                    ILLICIT = "moderation.providers.openai.sensitivity.illicit"
                    ILLICIT_VIOLENT = "moderation.providers.openai.sensitivity.illicit/violent"
                    SELF_HARM = "moderation.providers.openai.sensitivity.self-harm"
                    SELF_HARM_INTENT = "moderation.providers.openai.sensitivity.self-harm/intent"
                    SELF_HARM_INSTRUCTIONS = "moderation.providers.openai.sensitivity.self-harm/instructions"
                    VIOLENCE = "moderation.providers.openai.sensitivity.violence"
                    VIOLENCE_GRAPHIC = "moderation.providers.openai.sensitivity.violence/graphic"
        

    
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
    