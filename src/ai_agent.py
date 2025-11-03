# src/ai_agent.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from utils.config import settings
from utils.gemini_client import analyze_alert
from utils.kubectl_helper import perform_k8s_action
from utils.telegram_notify import send_message
from utils.log_helper import get_logger
import uvicorn
import traceback
import time

logger = get_logger("ai-agent")

app = FastAPI(title="AI DevOps Agent (Gemini Edition)")

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    # Could add readiness checks (DB, GEMINI connectivity) here
    return {"status": "ready"}

@app.post("/alert")
async def handle_alert(request: Request):
    """
    Expected Alertmanager webhook payload. Will:
    1. parse alert
    2. call Gemini to analyze
    3. decide action (scale/restart/none)
    4. perform action (if safe)
    5. notify via Telegram
    """
    try:
        payload = await request.json()
    except Exception:
        logger.exception("Failed to parse JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        alerts = payload.get("alerts")
        if not alerts:
            logger.warning("No alerts found in payload")
            raise HTTPException(status_code=400, detail="No alerts in payload")

        # For simplicity, process the first alert (can be extended to iterate)
        alert = alerts[0]

        status = alert.get("status", "firing")
        annotations = alert.get("annotations", {})
        labels = alert.get("labels", {})

        description = annotations.get("description") or annotations.get("summary") or str(alert)
        short_desc = description if len(description) < 800 else description[:800] + "..."

        logger.info("Received alert", extra={"status": status, "labels": labels, "description": short_desc})

        # 1. Analyze with Gemini
        start = time.time()
        analysis = analyze_alert(short_desc)
        elapsed = time.time() - start
        logger.info("Gemini analysis complete", extra={"elapsed_s": elapsed, "analysis_snippet": analysis[:200]})

        # 2. Decide and optionally act
        action_result = perform_k8s_action(analysis, labels)  # returns string describing action/result

        # 3. Construct notification to Telegram
        message = (
            f"🚨 *AI DevOps Monitor*\n\n"
            f"*Alert*: {labels.get('alertname','HighCPU')}\n"
            f"*Severity*: {labels.get('severity','warning')}\n"
            f"*Description*: {short_desc}\n\n"
            f"🧠 *AI Analysis*: {analysis}\n\n"
            f"{action_result}\n\n"
            f"_Processed in {elapsed:.2f}s_"
        )

        # 4. Send to Telegram (async-friendly simple call)
        send_message(message)

        return JSONResponse({"status": "processed", "action": action_result})

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unhandled error in /alert: %s", exc)
        logger.debug(traceback.format_exc())
        # Notify admins if needed
        try:
            send_message(f"⚠️ AI Agent error: {str(exc)}")
        except Exception:
            logger.exception("Failed to send error notification to Telegram")
        raise HTTPException(status_code=500, detail="Internal AI processing error")

if __name__ == "__main__":
    uvicorn.run("ai_agent:app", host="0.0.0.0", port=8000, log_level="info")
