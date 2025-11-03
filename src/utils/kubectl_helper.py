# src/utils/kubectl_helper.py
import subprocess
import shlex
from utils.log_helper import get_logger
from utils.config import settings

logger = get_logger("kubectl-helper")

# Try to import kubernetes python client; fallback to subprocess
try:
    from kubernetes import client, config as k8s_config
    k8s_available = True
    try:
        # In-cluster or KUBECONFIG
        k8s_config.load_incluster_config()
    except Exception:
        try:
            k8s_config.load_kube_config(config_file=settings.KUBECONFIG or None)
        except Exception:
            logger.warning("No kube config loaded; kubernetes client may fail until kubeconfig is available.")
except Exception:
    k8s_available = False

def _run_cmd(cmd):
    logger.info("Running shell command: %s", cmd)
    try:
        out = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT, text=True)
        logger.debug("Command output: %s", out)
        return True, out
    except subprocess.CalledProcessError as e:
        logger.error("Command failed: %s", e.output)
        return False, e.output

def perform_k8s_action(analysis_text: str, labels: dict) -> str:
    """
    Parse analysis text for AUTO: instructions or keywords and act accordingly.
    Returns a human-readable result string.
    """
    text = (analysis_text or "").lower()

    # Demo mode: simulate actions without touching Kubernetes
    if settings.DEMO_MODE:
        if "auto:" in text and "scale" in text and "deployment" in text:
            return "✅ (demo) Auto-scaled deployment `cpu-app` → 4 replicas."
        if "restart" in text or "rollout" in text:
            return "🔁 (demo) Restarted deployment `cpu-app`."
        return "ℹ️ (demo) No automated remediation performed."

    # Priority 1: explicit AUTO action from Gemini like: "AUTO: scale deployment cpu-app to 4"
    if "auto:" in text:
        try:
            # extract rest after AUTO:
            after = analysis_text.split("AUTO:")[1].strip()
            cmd_lower = after.lower()
            # naive parsing for scale
            if "scale" in cmd_lower and "deployment" in cmd_lower:
                # example: "scale deployment cpu-app to 4"
                parts = after.split()
                # find deployment name and replicas
                # simplistic parse:
                if "deployment" in parts:
                    idx = parts.index("deployment")
                    name = parts[idx+1]
                    # find 'to' then number
                    if "to" in parts:
                        to_idx = parts.index("to")
                        replicas = int(parts[to_idx+1])
                    else:
                        replicas = settings.DEFAULT_SCALE_REPLICAS
                    return _scale_deployment(name, replicas)
            if "restart" in cmd_lower and "deployment" in cmd_lower:
                # example: "restart deployment my-app"
                parts = after.split()
                if "deployment" in parts:
                    idx = parts.index("deployment")
                    name = parts[idx+1]
                    return _restart_deployment(name)
            # fallback run as kubectl command
            ok, out = _run_cmd(after)
            return f"✅ Ran AUTO action: {after}\nResult: {out}" if ok else f"⚠️ AUTO action failed: {out}"
        except Exception as e:
            logger.exception("Failed to perform AUTO action")
            return f"⚠️ Failed to perform AUTO action: {str(e)}"

    # Priority 2: heuristic keywords
    if "scale" in text and "deployment" in text:
        # try to scale the default deployment 'cpu-app'
        return _scale_deployment("cpu-app", settings.DEFAULT_SCALE_REPLICAS)

    if "restart" in text or "rollout" in text:
        return _restart_deployment("cpu-app")

    # If no clear action, return a safe message
    return "⚠️ No automated remediation performed. Manual review recommended."

def _scale_deployment(name: str, replicas: int) -> str:
    if k8s_available:
        try:
            apps_v1 = client.AppsV1Api()
            # patch scale
            body = {"spec": {"replicas": replicas}}
            apps_v1.patch_namespaced_deployment_scale(name=name, namespace="default", body={"spec":{"replicas":replicas}})
            logger.info("Scaled deployment %s → %d", name, replicas)
            return f"✅ Auto-scaled deployment `{name}` → {replicas} replicas."
        except Exception:
            logger.exception("Kubernetes client scale failed, falling back to kubectl")
            # fallback to kubectl
    # fallback:
    cmd = f"kubectl scale deployment {name} --replicas={replicas} -n default"
    ok, out = _run_cmd(cmd)
    return f"✅ Auto-scaled deployment `{name}` → {replicas} replicas." if ok else f"⚠️ Failed to scale deployment: {out}"

def _restart_deployment(name: str) -> str:
    if k8s_available:
        try:
            apps_v1 = client.AppsV1Api()
            # Using annotation patch as recommended
            body = {"spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": str(__import__('datetime').datetime.utcnow())}}}}}
            apps_v1.patch_namespaced_deployment(name=name, namespace="default", body=body)
            logger.info("Restarted deployment %s via kubernetes client", name)
            return f"🔁 Restarted deployment `{name}`."
        except Exception:
            logger.exception("Kubernetes client restart failed, falling back to kubectl")

    cmd = f"kubectl rollout restart deployment/{name} -n default"
    ok, out = _run_cmd(cmd)
    return f"🔁 Restarted deployment `{name}`." if ok else f"⚠️ Failed to restart deployment: {out}"
