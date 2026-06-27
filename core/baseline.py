from agents.base_agent import call_qwen

BASELINE_PROMPT = """You are a code reviewer. Review this PR diff and identify all issues.

Respond in this exact JSON format:
{
  "verdict": "APPROVE" | "REQUEST_CHANGES" | "BLOCK",
  "confidence": 0-100,
  "issues": [
    {
      "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
      "category": "security" | "performance" | "quality",
      "line": "line number or range",
      "description": "what the issue is",
      "fix": "how to fix it"
    }
  ],
  "summary": "one sentence summary"
}

Return raw JSON only, no markdown, no extra text."""

def single_agent_review(diff: str) -> dict:
    import json
    result = call_qwen(BASELINE_PROMPT, f"Review this PR diff:\n\n{diff}")
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"error": "parse failed", "raw": result}