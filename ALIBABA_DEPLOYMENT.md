# Alibaba Cloud Deployment

This document is a template: follow the steps below on your own Alibaba Cloud account, then fill in the **Proof of Deployment** section at the bottom before submitting to Devpost.

## Option A — ECS (recommended for this project)

The agent is a stateful interactive CLI, so a plain ECS instance running the container is the simplest honest deployment target (no need for EAS's model-serving machinery).

1. **Create an ECS instance**
   - Console → Elastic Compute Service → Create Instance
   - Recommended: `ecs.t6-c1m2.large` (2 vCPU / 4GB), Ubuntu 22.04, pay-as-you-go
   - Open only the ports you need (SSH/22); this agent has no inbound HTTP surface

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```

3. **Build and run the agent**
   ```bash
   git clone <this-repo-url>
   cd qwen-shariah-autopilot
   docker build -t qwen-shariah-autopilot .
   docker run -it --env-file .env qwen-shariah-autopilot
   ```
   (Add a `Dockerfile` — `FROM python:3.11-slim`, `COPY . .`, `RUN pip install -r requirements.txt`, `CMD ["python", "main.py"]` — if not already present.)

4. **Keep it running for a demo session** (optional, for judges who want to interact live)
   ```bash
   docker run -d --env-file .env --name autopilot qwen-shariah-autopilot tail -f /dev/null
   docker exec -it autopilot python main.py
   ```

## Option B — EAS (if you want a hosted inference-style endpoint)

EAS is built for model-serving workloads (a request/response HTTP endpoint), which is a different shape than this project's interactive CLI. If your hackathon submission wants an HTTP-accessible demo instead of a terminal session, that requires wrapping `agent/qwen_brain.run_conversation` in a small FastAPI app first, then deploying that app to EAS as a custom container processor. That wrapper is out of scope for the current phases — flag it if you want it built before deployment.

## Proof of Deployment

_Fill in after deploying:_

- **Deployment target:** ECS / EAS
- **Region:** `<e.g. ap-southeast-1>`
- **Instance ID / Service name:** `<...>`
- **Date deployed:** `<...>`
- **Screenshot or console link:** `<...>`
- **Demo access (if applicable):** `<public URL, or "SSH + terminal demo only">`
