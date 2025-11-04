# src/utils/gemini_client.py
import google.generativeai as genai
import os
from .log_helper import get_logger
from .config import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = get_logger("gemini-client")

# Configure GenAI client - supports GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS
_api_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY") or None
if _api_key and not settings.DEMO_MODE:
    genai.configure(api_key=_api_key)

# Cache the successfully resolved model name to avoid repeated discovery
_selected_model_name = None

def _resolve_model_name():
    global _selected_model_name
    if _selected_model_name:
        return _selected_model_name

    # Try configured name first
    candidate_models = [
        settings.GEMINI_MODEL,
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-001",
        "gemini-1.5-pro-latest",
    ]

    # Then attempt to discover any model that supports generateContent
    try:
        models = list(getattr(genai, "list_models", lambda: [])())
        for m in models:
            try:
                # google-generativeai models may expose supported_generation_methods
                methods = getattr(m, "supported_generation_methods", []) or []
                if "generateContent" in methods:
                    candidate_models.append(getattr(m, "name", None) or getattr(m, "model", None))
            except Exception:
                continue
    except Exception:
        # list_models can fail depending on key/permissions; ignore
        pass

    # Deduplicate while preserving order
    seen = set()
    candidate_models = [m for m in candidate_models if m and not (m in seen or seen.add(m))]
    logger.debug("Gemini candidate models: %s", candidate_models)
    _selected_model_name = candidate_models[0] if candidate_models else "gemini-1.5-flash-latest"
    return _selected_model_name

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
        last_exc = None
        # Build candidate list once per process; resolve and then try a few
        base_model = _resolve_model_name()
        dynamic_candidates = [base_model, "gemini-1.5-flash-001", "gemini-1.5-pro-latest"]
        seen = set()
        dynamic_candidates = [m for m in dynamic_candidates if m and not (m in seen or seen.add(m))]
        for model_name in dynamic_candidates:
            try:
                logger.debug("Trying Gemini model: %s", model_name)
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                text = getattr(resp, "text", None) or str(resp)
                text = text.strip()
                logger.debug("Gemini raw response: %s", text[:500])
                # Cache the working model
                global _selected_model_name
                _selected_model_name = model_name
                return text
            except Exception as model_exc:
                last_exc = model_exc
                continue
        raise last_exc or RuntimeError("No Gemini model succeeded")
    except Exception as e:
        logger.exception("Gemini client failed")
        raise
