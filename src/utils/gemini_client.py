# src/utils/gemini_client.py
import google.generativeai as genai
import os
from utils.log_helper import get_logger
from utils.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = get_logger("gemini-client")

# Configure GenAI client - supports GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS
_api_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or None
if _api_key and not settings.DEMO_MODE:
    genai.configure(api_key=_api_key)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10),
       retry=retry_if_exception_type(Exception))
def analyze_alert(description: str) -> str:
    """
    Send the alert description to Gemini and return concise analysis + recommended action.
    Retries on transient failures.
    """
    prompt = (
        "You are a reliable Site Reliability Engineer assistant.\n"
        "Analyze the following alert and provide:\n"
        "1) A one-sentence probable root cause.\n"
        "2) A concise recommended action (e.g., scale deployment, restart pods, investigate logs).\n"
        "3) If safe to auto-remediate, include the clear keyword 'AUTO: <action>' (e.g., 'AUTO: scale deployment cpu-app to 4').\n\n"
        f"Alert description:\n{description}\n\n"
        "Keep answer under 100 words and use plain, simple language."
    )

    # In demo mode or without API key, return a canned, deterministic response
    if settings.DEMO_MODE or not _api_key:
        logger.info("Gemini in demo/offline mode; returning canned analysis")
        return (
            "Probable cause: workload saturation due to increased traffic. "
            "Recommended: scale deployment 'cpu-app' to 4 replicas. AUTO: scale deployment cpu-app to 4"
        )

    logger.debug("Calling Gemini with prompt snippet: %s", prompt[:300])

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(prompt)
        text = getattr(resp, "text", None) or str(resp)
        text = text.strip()
        logger.debug("Gemini raw response: %s", text[:500])
        return text
    except Exception as e:
        logger.exception("Gemini client failed")
        raise
