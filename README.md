AI DevOps Cloud Monitor

Overview

This project provides an AI-assisted DevOps monitoring stack with a FastAPI agent integrating with Prometheus, Alertmanager, Kubernetes, Telegram notifications, and Grafana dashboards. It includes a Helm chart for Kubernetes deployment and raw Kubernetes manifests for quick starts.

Features

- FastAPI AI agent with health and Alertmanager webhook endpoints
- Telegram notifications for alerts
- Helpers to scale/restart Kubernetes workloads
- Helm chart (`helm/ai-monitor`) for deployment
- Sample Kubernetes manifests (`kubernetes/`)
- Grafana dashboards and Prometheus datasource templates (`grafana/`)

Quick Start (Local)

1. Create and fill `.env` from `.env.example`.
2. Create a virtual environment and install dependencies:
   - python -m venv .venv && source .venv/bin/activate
   - pip install -r requirements.txt
3. Run the service:
   - uvicorn src.ai_agent:app --host 0.0.0.0 --port 8080 --reload

Demo Mode (no external deps)

Run the agent with canned AI analysis and simulated Kubernetes actions. No Gemini API key, Telegram, or cluster required.

1. Set environment variable `DEMO_MODE=true` (and optionally port):
   - macOS/Linux:
     - DEMO_MODE=true uvicorn src.ai_agent:app --host 0.0.0.0 --port 8080 --reload
   - Docker:
     - docker build -t ai-devops-cloud-monitor:demo .
     - docker run -e DEMO_MODE=true -p 8080:8000 ai-devops-cloud-monitor:demo
2. In another shell, send the sample Alertmanager webhook:
   - curl -s -X POST http://localhost:8080/alert -H 'Content-Type: application/json' \
     --data @demo/sample-alert.json | jq .
3. Expected behavior:
   - The agent returns a response with an AI analysis and a simulated auto-scale action.
   - If Telegram is not configured, messages are skipped gracefully.

Docker

Build and run:

- docker build -t ai-devops-cloud-monitor:local .
- docker run --env-file .env -p 8080:8080 ai-devops-cloud-monitor:local

Kubernetes (Helm)

1. Ensure you have access to a cluster and `kubectl` context set.
2. Set values in `helm/ai-monitor/values.yaml` or rely on defaults.
3. Install chart:
   - helm upgrade --install ai-monitor helm/ai-monitor

Kubernetes (Manifests)

Apply raw manifests for a quick test:

- kubectl apply -f kubernetes/

Project Structure

- .env.example
- requirements.txt
- Dockerfile
- helm/ai-monitor
  - Chart.yaml, values.yaml, templates/
- kubernetes/
  - ai-agent-deployment.yaml, ai-agent-service.yaml, alert rules, alertmanager config, sample app
- src/
  - ai_agent.py, utils/
- grafana/
  - dashboards/, datasources/

License

MIT
