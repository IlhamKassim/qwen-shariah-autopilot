# Alibaba Cloud Deployment

## What's actually required

The Hackathon's legally-binding **Official Rules** (which explicitly state they prevail over any other Hackathon materials in case of conflict — see Official Rules §11) define Proof of Alibaba Cloud Deployment as:

> "Include Proof of Alibaba Cloud Deployment: You must demonstrate that the backend is running on Alibaba Cloud. Proof must be a link to a code file in their code repo that demonstrates use of Alibaba Cloud services and APIs."

This is satisfied by a **code-file link — no paid cloud hosting required.** Qwen Cloud is Alibaba Cloud's own model service (Alibaba Cloud is the Hackathon's Sponsor per Official Rules §2), so calling it from this codebase already qualifies.

**The proof link for this project:** [`agent/qwen_brain.py`](agent/qwen_brain.py), specifically:

```python
_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
_MODEL = "qwen3.7-max"
```

and the `_client()` function that constructs the OpenAI SDK client against that Alibaba Cloud endpoint. Paste that file's GitHub URL directly into the Devpost submission form field for this requirement.

(An earlier, less-official "Proof of Deploy" quickstart PDF circulated for this hackathon suggested a screenshot of a real running Alibaba Cloud instance — e.g. via ECS or Simple Application Server (SAS). That is **not required** per the Official Rules, and is not pursued in this project.)

## Optional: real hosting, if you want it anyway

If you later want an actual deployed instance (e.g. for a more impressive demo, or because "Technical Depth & Engineering" judging might reward extra infrastructure sophistication), SAS is the fastest path — the hackathon's own quickstart guide recommends it over ECS for exactly this project's shape (external LLM API calls, no local GPU, individual developer). This is a nice-to-have, not a submission blocker.

<details>
<summary>SAS deployment steps (optional)</summary>

1. Go to the [SAS Console](https://swas.console.alibabacloud.com) (Alibaba Cloud International — separate account from Qwen Cloud) → **Create Server**
2. Pick a region, choose the pre-installed **Docker** application image
3. Pick the smallest plan, complete payment
4. Reset the root password from the console
5. Connect via **Workbench** (one-click browser terminal)
6. ```bash
   docker --version   # confirm Docker's ready
   git clone https://github.com/IlhamKassim/qwen-shariah-autopilot.git
   cd qwen-shariah-autopilot
   docker build -t qwen-shariah-autopilot .
   nano .env           # paste real Alpaca + Qwen credentials
   docker run -it --env-file .env qwen-shariah-autopilot
   ```
7. No inbound ports needed beyond SAS's defaults — this agent has no HTTP server surface.

</details>
