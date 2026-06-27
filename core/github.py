import os, requests
from dotenv import load_dotenv
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_pr_diff(repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    response = requests.get(
        url,
        headers={**HEADERS, "Accept": "application/vnd.github.v3.diff"}
    )
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR diff: {response.status_code} {response.text}")
    return response.text

def post_comment(repo: str, pr_number: int, verdict: dict) -> bool:
    import json
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    
    final = verdict.get("final", {})
    round1 = verdict.get("round1", [])
    round2 = verdict.get("round2", [])
    
    verdict_emoji = {
        "APPROVE": "✅",
        "REQUEST_CHANGES": "⚠️",
        "BLOCK": "🚫"
    }.get(final.get("final_verdict", ""), "❓")

    agent_rows = ""
    for r1, r2 in zip(round1, round2):
        name = r1.get("agent", "Unknown")
        v1 = r1.get("verdict", "?")
        v2 = r2.get("updated_verdict", "?")
        conf = r2.get("updated_confidence", "?")
        agent_rows += f"| {name} | {v1} | {v2} | {conf}% |\n"

    disagreements = ""
    for agent in round2:
        name = agent.get("agent", "")
        for d in agent.get("disagreements", []):
            disagreements += f"- **{name}** disagreed with **{d.get('with_agent')}**: {d.get('reason', '')}\n"

    issues_text = ""
    for i, issue in enumerate(final.get("priority_issues", []), 1):
        severity = issue.get("severity", "")
        desc = issue.get("description", "")
        fix = issue.get("fix", "")
        agent = issue.get("from_agent", "")
        issues_text += f"{i}. **[{severity}]** ({agent}) {desc}\n   - 💡 Fix: {fix}\n\n"

    comment = f"""## {verdict_emoji} CodeCouncil Review — {final.get("final_verdict", "UNKNOWN")}

> {final.get("summary", "")}

---

### 🗳️ Agent Verdicts

| Agent | Round 1 | Round 2 | Confidence |
|-------|---------|---------|------------|
{agent_rows}
---

### ⚔️ Key Debates
{disagreements if disagreements else "Agents were in full agreement."}

---

### 🏆 Who Won the Debate
{final.get("who_won_debate", "N/A")}

---

### 🔴 Priority Issues
{issues_text if issues_text else "No critical issues found."}

---

### 📊 TechLead Reasoning
{final.get("reasoning", "")}

---
*Powered by CodeCouncil — Multi-Agent PR Review System*
"""

    response = requests.post(url, headers=HEADERS, json={"body": comment})
    return response.status_code == 201

def get_pr_info(repo: str, pr_number: int) -> dict:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR info: {response.status_code}")
    return response.json()