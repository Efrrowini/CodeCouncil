import os, hmac, hashlib, json
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from core.debate import run_debate
from core.github import get_pr_diff, post_comment
from core.memory import get_memory_summary

load_dotenv()

app = FastAPI(title="CodeCouncil", version="2.0.0")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "codecouncil123")

def verify_signature(payload: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def process_pr(repo: str, pr_number: int):
    try:
        print(f"\n🔍 Fetching PR #{pr_number} from {repo}...")
        diff = get_pr_diff(repo, pr_number)

        if len(diff) > 8000:
            diff = diff[:8000]
            print("⚠️ Diff truncated to 8000 chars")

        print(f"📄 Diff fetched ({len(diff)} chars). Starting debate...")
        verdict = run_debate(diff, repo=repo)

        print("💬 Posting comment to GitHub...")
        success = post_comment(repo, pr_number, verdict)
        from core.slack import send_slack_notification
        send_slack_notification(repo, pr_number, verdict)

        if success:
            print(f"✅ Comment posted to PR #{pr_number}")
        else:
            print(f"❌ Failed to post comment to PR #{pr_number}")

    except Exception as e:
        print(f"❌ Error processing PR #{pr_number}: {e}")

@app.get("/")
def health():
    return {
        "status": "CodeCouncil running",
        "version": "2.0.0",
        "agents": ["SecurityAuditor", "PerfEngineer", "CleanCodeReviewer", "TechLead"],
        "features": ["parallel execution", "debate rounds", "conflict detection", "confidence calibration", "PR memory"]
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event")
    data = json.loads(payload)

    if event == "pull_request" and data.get("action") in ["opened", "synchronize"]:
        repo = data["repository"]["full_name"]
        pr_number = data["pull_request"]["number"]
        pr_title = data["pull_request"]["title"]

        print(f"\n📥 PR received: #{pr_number} — {pr_title}")
        background_tasks.add_task(process_pr, repo, pr_number)

        return {
            "status": "processing",
            "pr": pr_number,
            "repo": repo,
            "message": "Debate started in background"
        }

    return {"status": "ignored", "event": event}

@app.post("/api/review")
async def api_review(request: Request):
    data = await request.json()
    repo = data.get("repo")
    pr_number = data.get("pr_number")

    if not repo or not pr_number:
        raise HTTPException(status_code=400, detail="repo and pr_number required")

    diff = get_pr_diff(repo, int(pr_number))
    if len(diff) > 8000:
        diff = diff[:8000]

    verdict = run_debate(diff, repo=repo)
    post_comment(repo, int(pr_number), verdict)
    return verdict

@app.get("/memory/{owner}/{repo_name}")
async def get_memory(owner: str, repo_name: str):
    repo = f"{owner}/{repo_name}"
    summary = get_memory_summary(repo)
    return summary