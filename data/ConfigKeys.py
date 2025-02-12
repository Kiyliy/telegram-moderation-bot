class ConfigKeys:
    class database:
        DAILY_POINTS: str = 'database.daily_points'
        PERMANENT_POINTS: str = 'database.permanent_points'
    
    class bot:
        ADMIN_IDS: str = 'bot.admin_ids'
        
        class settings:
            class moderation:
                class rules:
                    NSFW: str = 'bot.settings.moderation.rules.nsfw'
                    VIOLENCE: str = 'bot.settings.moderation.rules.violence'
                    POLITICAL: str = 'bot.settings.moderation.rules.political'
                    SPAM: str = 'bot.settings.moderation.rules.spam'
                
                class sensitivity:
                    NSFW: str = 'bot.settings.moderation.sensitivity.nsfw'
                    VIOLENCE: str = 'bot.settings.moderation.sensitivity.violence'
                    POLITICAL: str = 'bot.settings.moderation.sensitivity.political'
                    SPAM: str = 'bot.settings.moderation.sensitivity.spam'
                
                class auto_actions:
                    DELETE_MESSAGE: str = 'bot.settings.moderation.auto_actions.delete_message'
                    WARN_USER: str = 'bot.settings.moderation.auto_actions.warn_user'
                    NOTIFY_ADMINS: str = 'bot.settings.moderation.auto_actions.notify_admins'
            
            class warning_messages:
                NSFW: str = 'bot.settings.warning_messages.nsfw'
                VIOLENCE: str = 'bot.settings.warning_messages.violence'
                POLITICAL: str = 'bot.settings.warning_messages.political'
                SPAM: str = 'bot.settings.warning_messages.spam'
            
            class punishment:
                MUTE_DURATIONS: str = 'bot.settings.punishment.mute_durations'
                BAN_THRESHOLD: str = 'bot.settings.punishment.ban_threshold'
        