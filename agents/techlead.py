from agents.base_agent import call_qwen

SYSTEM_PROMPT = """You are TechLead, the final decision maker on this PR review council.
You will receive the opinions of 3 specialist agents: SecurityAuditor, PerfEngineer, CleanCodeReviewer.
Your job is to weigh their arguments and make the final verdict.

You must respond in this exact JSON format:
{
  "agent": "TechLead",
  "final_verdict": "APPROVE" | "REQUEST_CHANGES" | "BLOCK",
  "confidence": 0-100,
  "reasoning": "explain why you sided with certain agents over others",
  "priority_issues": [
    {
      "from_agent": "agent name",
      "severity": "severity level",
      "description": "issue description",
      "fix": "recommended fix"
    }
  ],
  "summary": "final one sentence verdict for the PR author"
}

Rules:
- BLOCK only if SecurityAuditor finds CRITICAL security issues
- REQUEST_CHANGES for quality/performance issues without critical security flaws
- Weight SecurityAuditor highest, then PerfEngineer, then CleanCodeReviewer
- Do NOT escalate to BLOCK just because multiple agents agree on quality issues
- If agents disagree, explain who you sided with and why
Return raw JSON only, no markdown, no extra text."""


def arbitrate(diff: str, agent_opinions: list) -> dict:
    import json
    opinions_text = "\n\n".join([
        f"=== {op.get('agent', 'Unknown')} ===\n{json.dumps(op, indent=2)}"
        for op in agent_opinions
    ])
    user_message = f"""PR Diff:
{diff}

Agent Opinions:
{opinions_text}

Make your final verdict."""

    result = call_qwen(SYSTEM_PROMPT, user_message, model="qwen-plus")
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"agent": "TechLead", "error": "parse failed", "raw": result}


def arbitrate_full(diff: str, round1: list, round2: list) -> dict:
    import json

    FULL_PROMPT = """You are TechLead, the final decision maker on this PR review council.
You will see TWO rounds of agent debate:
- Round 1: Each agent's independent analysis
- Round 2: Each agent's response to the others — agreements, disagreements, rebuttals

Your job is to read the full debate and make the final verdict.

You must respond in this exact JSON format:
{
  "agent": "TechLead",
  "final_verdict": "APPROVE" | "REQUEST_CHANGES" | "BLOCK",
  "confidence": 0-100,
  "debate_summary": "summarize the key points of disagreement between agents",
  "who_won_debate": "which agent made the strongest arguments and why",
  "reasoning": "explain your final verdict based on the full debate",
  "priority_issues": [
    {
      "from_agent": "agent name",
      "severity": "severity level",
      "description": "issue description",
      "fix": "recommended fix"
    }
  ],
  "summary": "final one sentence verdict for the PR author"
}

Rules:
- BLOCK only if SecurityAuditor finds CRITICAL security issues
- REQUEST_CHANGES for quality/performance issues without critical security flaws
- Weight SecurityAuditor highest, then PerfEngineer, then CleanCodeReviewer
- Do NOT escalate to BLOCK just because multiple agents agree on quality issues
- If agents disagree, explain who you sided with and why
Return raw JSON only, no markdown, no extra text."""

    round1_text = "\n\n".join([
        f"=== {op.get('agent', 'Unknown')} (Round 1) ===\n{json.dumps(op, indent=2)}"
        for op in round1
    ])
    round2_text = "\n\n".join([
        f"=== {op.get('agent', 'Unknown')} (Round 2) ===\n{json.dumps(op, indent=2)}"
        for op in round2
    ])

    user_message = f"""PR Diff:
{diff}

=== ROUND 1: Independent Analysis ===
{round1_text}

=== ROUND 2: Debate and Rebuttals ===
{round2_text}

Make your final verdict based on the full debate."""

    result = call_qwen(FULL_PROMPT, user_message, model="qwen-plus")
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"agent": "TechLead", "error": "parse failed", "raw": result}