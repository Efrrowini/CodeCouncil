# CodeCouncil — Multi-Agent PR Review System

> Built for the Global AI Hackathon with Qwen Cloud (Track 3: Agent Society)

## What is CodeCouncil?
CodeCouncil is a multi-agent PR review system where 4 specialized AI agents debate pull requests and produce a consensus verdict.

## Agents
- 🔴 **SecurityAuditor** — finds vulnerabilities, SQL injection, hardcoded secrets
- 🟡 **PerfEngineer** — detects N+1 queries, complexity issues, memory leaks  
- 🟢 **CleanCodeReviewer** — enforces naming, SOLID principles, code quality
- 🟣 **TechLead** — reads the full debate and makes the final verdict

## How it works
1. PR opened on GitHub → webhook fires
2. All 3 specialist agents analyze independently (Round 1)
3. Agents read each other's opinions and debate (Round 2)
4. TechLead arbitrates and posts verdict to GitHub PR (Round 3)

## Proof of Alibaba Cloud Usage
This project uses Qwen Cloud (Alibaba Cloud) APIs via:
- API endpoint: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- Models used: `qwen-plus` (specialist agents), `qwen-plus` (TechLead)
- See: [agents/base_agent.py](agents/base_agent.py)

## Benchmark Results
CodeCouncil vs Single-Agent baseline:
- **+22% issue detection rate**
- **2x more issues found** per PR (5.3 vs 2.7 average)
- Full results: [benchmark_results.json](benchmark_results.json)

## Setup
```bash
git clone https://github.com/Efrrowini/CodeCouncil.git
cd CodeCouncil
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
uvicorn main:app --reload --port 8000
```

## Architecture
- **FastAPI** — webhook receiver and API gateway
- **Qwen Cloud** — powers all 4 agents via OpenAI-compatible API
- **GitHub API** — fetches PR diffs and posts review comments
- **Multi-round debate** — 3 rounds of agent interaction

## Track
Track 3: Agent Society
