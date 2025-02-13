from dotenv import load_dotenv
import os

load_dotenv()

class ModerationConfig:
    """审核配置"""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODERATION_MODEL = os.getenv("OPENAI_MODERATION_MODEL", "omni-moderation-latest")
    VIDEO_FRAME_INTERVAL = int(os.getenv("VIDEO_FRAME_INTERVAL", "30")) 
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
