# src/utils/config.py
import os
from dataclasses import dataclass

@dataclass
class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    KUBECONFIG: str = os.getenv("KUBECONFIG", "")
    DEFAULT_SCALE_REPLICAS: int = int(os.getenv("DEFAULT_SCALE_REPLICAS", "4"))
    AUTO_REMEDIATE: bool = os.getenv("AUTO_REMEDIATE", "true").lower() in ("1","true","yes")
    # tune timeout/retry behavior here
    TELEGRAM_RETRY_COUNT: int = int(os.getenv("TELEGRAM_RETRY_COUNT", "3"))
    # demo mode: skip external calls and use canned outputs
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("1","true","yes")

settings = Settings()
