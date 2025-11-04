## AI DevOps Cloud Monitor

### Overview

This project provides an AI-assisted DevOps monitoring stack. A FastAPI agent receives Alertmanager webhooks, summarizes context via Google Gemini, optionally auto-remediates Kubernetes workloads (scale/restart), and posts summaries to Telegram. It includes Helm charts, raw Kubernetes manifests, and Grafana dashboards.

### Features

- FastAPI AI agent with `/healthz`, `/readyz`, and `/alert` endpoints
- Gemini-based analysis with model auto-discovery and configurable `GEMINI_MODEL`
- Auto-remediation helpers to scale/restart Kubernetes deployments
- Telegram notifications (optional)
- Helm chart (`helm/ai-monitor`) and raw manifests (`kubernetes/`)
- Grafana dashboards and Prometheus datasource templates (`grafana/`)

### Architecture (high level)

- Alertmanager → HTTP POST to agent `/alert`
- Agent → summarize using Gemini → decide action → optional K8s change → Telegram notify
- Actions use Kubernetes Python client first, falling back to `kubectl` if needed

### Requirements

- Python 3.10+ recommended (3.12 preferred). 3.9 works but prints legacy warnings.
- `kubectl` configured if you want real remediation.
- Optional: Gemini API key (`GOOGLE_API_KEY` or `GEMINI_API_KEY`), Telegram bot token/chat id.

### Environment variables (.env)

- `GOOGLE_API_KEY` or `GEMINI_API_KEY`: Gemini access (omit for demo mode)
- `GEMINI_MODEL` (optional): e.g. `gemini-2.5-flash` (auto-discovery is built-in)
- `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (optional)
- `KUBECONFIG`: path to kubeconfig (defaults to standard locations)
- `DEFAULT_SCALE_REPLICAS` (int, default 4)
- `AUTO_REMEDIATE` (true/false, default true)
- `DEMO_MODE` (true/false, default false)

### Local Setup

1) Create venv and install deps

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

2) Create `.env` (optional for demo)

```bash
cp .env.example .env  # if provided; otherwise create with keys you need
# minimally for real mode:
# GOOGLE_API_KEY=...
# TELEGRAM_TOKEN=...
# TELEGRAM_CHAT_ID=...
```

### Run (Local)

- Real mode (recommended on Python 3.10+):

```bash
python3 -m uvicorn src.ai_agent:app --host 0.0.0.0 --port 8080
```

- Demo mode (no external deps):

```bash
DEMO_MODE=true python3 -m uvicorn src.ai_agent:app --host 0.0.0.0 --port 8080
```

### End-to-End Test (Local)

1) Start the agent (real or demo as above)
2) Send a sample Alertmanager webhook:

```bash
curl -s -X POST http://localhost:8080/alert \
  -H 'Content-Type: application/json' \
  --data @demo/sample-alert.json | jq .
```

3) Expected:
- Response contains `{"status":"processed", "action": ...}`
- Logs show Gemini analysis; in real mode, a current model is auto-selected
- If Kubernetes is reachable and `cpu-app` exists, a scale/restart action may occur
- If Telegram configured, a message is sent; otherwise it is skipped gracefully

### Docker

Build and run:

```bash
docker build -t ai-devops-cloud-monitor:local .
docker run --env-file .env -p 8080:8080 ai-devops-cloud-monitor:local
```

#### Demo via Docker:

```bash
docker build -t ai-devops-cloud-monitor:demo .
docker run -e DEMO_MODE=true -p 8080:8000 ai-devops-cloud-monitor:demo
```

### Kubernetes via Manifests (quick test)

```bash
kubectl apply -f kubernetes/
# or minimally deploy the sample app if you only want to test remediation
kubectl apply -f kubernetes/sample-app-deployment.yaml

# If running the agent locally against a cluster, ensure kubectl works and KUBECONFIG is set
export KUBECONFIG="$HOME/.kube/config"
kubectl get deploy cpu-app -n default
```

#### Bring up sample cpu-app (kubectl steps)

```bash
# 1) Point kubectl at your cluster
export KUBECONFIG="$HOME/.kube/config"
kubectl config current-context

# 2) Ensure the target namespace exists (default is fine)
kubectl get ns

# 3) Deploy the sample cpu-app workload
kubectl apply -f kubernetes/sample-app-deployment.yaml

# 4) Wait for rollout to complete
kubectl rollout status deploy/cpu-app -n default
kubectl get deploy cpu-app -n default

# 5) (Optional) Inspect pods
kubectl get pods -l app=cpu-app -n default
kubectl logs -l app=cpu-app -n default --tail=100

# 6) (Optional) Generate some load to trigger CPU usage (adjust as needed)
# kubectl run loadgen --rm -it --image=busybox --restart=Never -- sh -c \
#   'i=0; while [ $i -lt 200000 ]; do i=$((i+1)); done; echo done'

# 7) Verify the agent scales cpu-app after an alert (send sample alert to agent)
curl -s -X POST http://localhost:8080/alert \
  -H 'Content-Type: application/json' \
  --data @demo/sample-alert.json | jq .

# 8) Confirm replicas changed (if AUTO action decided to scale)
kubectl get deploy cpu-app -n default -o jsonpath='{.spec.replicas}{"\n"}'
```

### Kubernetes via Helm

```bash
helm upgrade --install ai-monitor helm/ai-monitor
```

### Grafana

- Import JSON from `grafana/dashboards/`
- Configure Prometheus using `grafana/datasources/prometheus-datasource.yaml` (or your platform’s preferred method)

### Troubleshooting

- Port in use: `lsof -i :8080` then `kill -9 <PID>`
- Python 3.9 warnings: upgrade to Python 3.10+ to remove legacy messages
- Gemini model 404: set `GEMINI_MODEL` to a model enabled for your key (e.g., `gemini-2.5-flash`), or rely on auto-discovery
- Kubernetes 404 "deployment not found": deploy the sample `cpu-app` or adjust the target name/namespace
- No kube config: set `KUBECONFIG=$HOME/.kube/config` or run in-cluster
- Disable auto-remediation while testing: `AUTO_REMEDIATE=false`

### Project Structure

- `.env.example` (if provided)
- `requirements.txt`
- `Dockerfile`
- `helm/ai-monitor` (Chart, templates)
- `kubernetes/` (agent/service/alert rules/alertmanager config/sample app)
- `src/` (FastAPI app and utils)
- `grafana/` (dashboards and datasource)

### License

MIT
