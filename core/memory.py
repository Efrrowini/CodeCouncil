import json
import os
from datetime import datetime

MEMORY_FILE = "pr_memory.json"

def load_memory() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(memory: dict):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)

def store_review(repo: str, pr_number: int, verdict: dict, conflicts: list, calibration: list):
    memory = load_memory()
    
    if repo not in memory:
        memory[repo] = {
            "total_reviews": 0,
            "recurring_issues": {},
            "agent_track_record": {
                "SecurityAuditor": {"blocks": 0, "approves": 0},
                "PerfEngineer": {"blocks": 0, "approves": 0},
                "CleanCodeReviewer": {"blocks": 0, "approves": 0}
            },
            "reviews": []
        }
    
    final = verdict.get("final", {})
    round1 = verdict.get("round1", [])
    
    for agent in round1:
        name = agent.get("agent", "")
        v = agent.get("verdict", "APPROVE")
        if name in memory[repo]["agent_track_record"]:
            if v == "BLOCK":
                memory[repo]["agent_track_record"][name]["blocks"] += 1
            else:
                memory[repo]["agent_track_record"][name]["approves"] += 1
    
    for agent in round1:
        for issue in agent.get("issues", []):
            category = issue.get("severity", "LOW") + ":" + issue.get("description", "")[:50]
            desc_lower = issue.get("description", "").lower()
            
            issue_type = categorize_issue(desc_lower)
            if issue_type:
                memory[repo]["recurring_issues"][issue_type] = \
                    memory[repo]["recurring_issues"].get(issue_type, 0) + 1
    
    review_entry = {
        "pr_number": pr_number,
        "date": datetime.now().isoformat(),
        "final_verdict": final.get("final_verdict", "UNKNOWN"),
        "confidence": final.get("confidence", 0),
        "conflicts_detected": len(conflicts),
        "issue_count": len(final.get("priority_issues", [])),
        "summary": final.get("summary", "")
    }
    
    memory[repo]["reviews"].append(review_entry)
    memory[repo]["total_reviews"] += 1
    
    if len(memory[repo]["reviews"]) > 20:
        memory[repo]["reviews"] = memory[repo]["reviews"][-20:]
    
    save_memory(memory)

def categorize_issue(desc: str) -> str:
    if any(w in desc for w in ["sql injection", "sqli", "injection"]):
        return "sql_injection"
    if any(w in desc for w in ["hardcoded", "api key", "secret", "password", "credential"]):
        return "hardcoded_secret"
    if any(w in desc for w in ["n+1", "n + 1", "query in loop"]):
        return "n_plus_1_query"
    if any(w in desc for w in ["xss", "cross-site"]):
        return "xss"
    if any(w in desc for w in ["naming", "readability", "variable name"]):
        return "poor_naming"
    if any(w in desc for w in ["error handling", "exception", "try/except"]):
        return "missing_error_handling"
    if any(w in desc for w in ["auth", "authorization", "authentication"]):
        return "auth_issue"
    return ""

def get_repo_context(repo: str) -> str:
    memory = load_memory()
    
    if repo not in memory or memory[repo]["total_reviews"] == 0:
        return ""
    
    repo_data = memory[repo]
    total = repo_data["total_reviews"]
    recurring = repo_data["recurring_issues"]
    track = repo_data["agent_track_record"]
    recent = repo_data["reviews"][-3:] if repo_data["reviews"] else []
    
    context_parts = [f"REPO HISTORY ({repo}): {total} previous PR reviews."]
    
    if recurring:
        sorted_issues = sorted(recurring.items(), key=lambda x: x[1], reverse=True)
        top_issues = sorted_issues[:3]
        issue_str = ", ".join([f"{k.replace('_', ' ')} ({v}x)" for k, v in top_issues])
        context_parts.append(f"Recurring issues in this repo: {issue_str}.")
    
    if recent:
        block_count = sum(1 for r in recent if r["final_verdict"] == "BLOCK")
        context_parts.append(f"Last {len(recent)} PRs: {block_count} blocked.")
    
    sec_blocks = track["SecurityAuditor"]["blocks"]
    if sec_blocks > 2:
        context_parts.append(f"SecurityAuditor has blocked {sec_blocks} PRs in this repo — high-risk codebase.")
    
    return " ".join(context_parts)

def get_memory_summary(repo: str) -> dict:
    memory = load_memory()
    if repo not in memory:
        return {"total_reviews": 0, "recurring_issues": {}, "reviews": []}
    return memory[repo]