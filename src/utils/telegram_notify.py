# src/utils/telegram_notify.py
import requests
import time
from .config import settings
from .log_helper import get_logger

logger = get_logger("telegram")

def send_message(text: str, parse_mode: str = "Markdown"):
    """
    Send a message to configured TELEGRAM_CHAT_ID using TELEGRAM_TOKEN.
    Retries on transient network issues.
    """
    token = settings.TELEGRAM_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        logger.warning("Telegram not configured (missing token/chat_id). Message skipped.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}

    attempts = settings.TELEGRAM_RETRY_COUNT or 3
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Sent telegram message (len=%d)", len(text))
                return True
            else:
                logger.warning("Telegram send failed (status=%s): %s", resp.status_code, resp.text)
        except Exception as e:
            logger.warning("Telegram send exception (attempt %d): %s", attempt, str(e))
        time.sleep(2 ** attempt)
    logger.error("Failed to send telegram message after %d attempts", attempts)
    return False
