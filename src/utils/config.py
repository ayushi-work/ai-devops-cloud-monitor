# src/utils/config.py
import os
from typing import Optional
try:
    # Load variables from a .env file if present (local/dev convenience)
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # If python-dotenv isn't installed, proceed with OS env vars only
    pass
from dataclasses import dataclass

@dataclass
class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
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
