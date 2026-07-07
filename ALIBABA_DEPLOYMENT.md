# Alibaba Cloud Deployment

The hackathon's submission checklist requires **Proof of Alibaba Cloud Deployment**, specifically: *"Find your Workbench Overview and take a screenshot of the running project."* This means a real cloud instance running the agent, screenshotted from Alibaba Cloud's own browser-based Workbench console — a code-file link alone is not sufficient.

This document is a template: follow the steps below on your own Alibaba Cloud account, then fill in the **Proof of Deployment** section at the bottom before submitting to Devpost.

## Recommended: SAS (Simple Application Server), not ECS

The hackathon's own deployment guide recommends SAS over ECS for exactly this project's shape: *"Your agent calls external LLM APIs (no local GPU needed)... You're an individual developer, student, or small team... You want to deploy in under 5 minutes."* ECS is worth it instead only if you need GPU inference, auto-scaling, or high concurrency — none of which apply here (this agent just makes outbound calls to Qwen Cloud and Alpaca/yfinance).

### Steps

1. **Create the instance**
   - Go to the [SAS Console](https://swas.console.alibabacloud.com) (this is Alibaba Cloud International — a separate account/login from Qwen Cloud, sign up there first if you haven't) → **Create Server**
   - Pick a region, then under **Image**, choose the pre-installed **Docker** application image (fastest — skips manual Docker install)
   - Pick the smallest plan (this agent is lightweight — no GPU, no heavy compute)
   - Complete payment; the instance provisions immediately with a public IP

2. **Reset the root password**
   - SAS instances ship with no default password — do this from the console under **Reset Password** before connecting

3. **Connect via Workbench**
   - Click **Connect** on the instance card → opens a one-click browser terminal, no SSH client or password needed
   - This is also where you'll take the required screenshot later

4. **Verify Docker is ready**
   ```bash
   docker --version
   docker compose version
   ```

5. **Clone and build**
   ```bash
   git clone https://github.com/IlhamKassim/qwen-shariah-autopilot.git
   cd qwen-shariah-autopilot
   docker build -t qwen-shariah-autopilot .
   ```

6. **Add your `.env`** (paste real Alpaca + Qwen credentials — never commit this file)
   ```bash
   nano .env   # or vi/vim
   ```

7. **Run the agent interactively**
   ```bash
   docker run -it --env-file .env qwen-shariah-autopilot
   ```
   Ask it something (e.g. "Analyze the portfolio and tell me if we should rebalance") so the Workbench terminal shows the agent actually working, not just an idle prompt.

8. **Take the required screenshot**
   - While the agent is running (or just finished a real response) in the Workbench terminal, screenshot the **Workbench Overview** page — it should show both Alibaba Cloud's own console chrome and the running agent's terminal output in the same frame. This is the proof judges are asking for.

9. **Open only the ports you need**
   - This agent has no inbound HTTP surface (it's a terminal CLI, not a server) — SAS's default firewall rules (22, 80, 443) are more than sufficient; you don't need to open anything extra for this project.

## Alternative: ECS

Only worth it if you specifically want a persistent, always-on demo instance rather than an on-demand Workbench session. The steps are the same shape (create instance → install Docker → clone/build/run), just with more manual VPC/security-group setup than SAS requires. See the hackathon's own "How To Deploy on Alibaba Cloud" (ECS) section if you go this route.

## Proof of Deployment

_Fill in after deploying:_

- **Deployment target:** SAS / ECS
- **Region:** `<e.g. ap-southeast-1>`
- **Instance ID:** `<...>`
- **Date deployed:** `<...>`
- **Workbench Overview screenshot:** `<link or attach to Devpost submission>`
