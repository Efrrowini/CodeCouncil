import json
import concurrent.futures
from agents import security, performance, cleancode, techlead
from agents.base_agent import call_qwen
from core.conflict import detect_conflicts, calculate_calibration, debate_impact_score
from core.memory import get_repo_context, store_review

def run_debate(diff: str, repo: str = "") -> dict:
    repo_context = get_repo_context(repo) if repo else ""
    
    if repo_context:
        print(f"  Memory context: {repo_context[:100]}...")
        enriched_diff = f"{diff}\n\n[REPO CONTEXT: {repo_context}]"
    else:
        enriched_diff = diff

    print("=== ROUND 1: Independent Analysis (parallel) ===")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        sec_future = executor.submit(security.review, enriched_diff)
        perf_future = executor.submit(performance.review, enriched_diff)
        clean_future = executor.submit(cleancode.review, enriched_diff)

        sec = sec_future.result()
        perf = perf_future.result()
        clean = clean_future.result()

    round1 = [sec, perf, clean]

    print("=== ROUND 2: Debate (parallel) ===")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        sec_future = executor.submit(debate_response, diff, sec, [perf, clean])
        perf_future = executor.submit(debate_response, diff, perf, [sec, clean])
        clean_future = executor.submit(debate_response, diff, clean, [sec, perf])

        sec_rebuttal = sec_future.result()
        perf_rebuttal = perf_future.result()
        clean_rebuttal = clean_future.result()

    round2 = [sec_rebuttal, perf_rebuttal, clean_rebuttal]

    print("=== ROUND 3: TechLead Final Verdict ===")
    final = techlead.arbitrate_full(diff, round1, round2)

    print("=== ANALYZING DEBATE QUALITY ===")
    conflicts = detect_conflicts(round1, round2)
    calibrations = calculate_calibration(round1, round2)
    impact = debate_impact_score(conflicts, calibrations)

    result = {
        "round1": round1,
        "round2": round2,
        "final": final,
        "conflicts": conflicts,
        "calibration": calibrations,
        "debate_impact": impact,
        "repo_context": repo_context
    }

    if repo:
        store_review(repo, 0, result, conflicts, calibrations)

    return result


def debate_response(diff: str, my_opinion: dict, other_opinions: list) -> dict:
    agent_name = my_opinion.get("agent", "Unknown")

    others_text = "\n\n".join([
        f"=== {op.get('agent', 'Unknown')} said ===\n{json.dumps(op, indent=2)}"
        for op in other_opinions
    ])

    system_prompt = f"""You are {agent_name}. You have already reviewed a PR diff.
Now you can see what your fellow reviewers said.
You must respond to their points — agree or disagree with specific reasoning.

Respond in this exact JSON format:
{{
  "agent": "{agent_name}",
  "round": 2,
  "agreements": [
    {{
      "with_agent": "agent name",
      "point": "what you agree with",
      "reason": "why you agree"
    }}
  ],
  "disagreements": [
    {{
      "with_agent": "agent name",
      "point": "what you disagree with",
      "reason": "why you disagree from your specialist perspective"
    }}
  ],
  "new_findings": "any new issues you noticed after seeing other perspectives",
  "updated_verdict": "APPROVE" | "REQUEST_CHANGES" | "BLOCK",
  "updated_confidence": 0-100
}}

Be a specialist — disagree when other agents venture outside their domain.
Return raw JSON only, no markdown, no extra text."""

    user_message = f"""Your original review:
{json.dumps(my_opinion, indent=2)}

What other agents said:
{others_text}

Now respond to their points."""

    result = call_qwen(system_prompt, user_message)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"agent": agent_name, "round": 2, "error": "parse failed", "raw": result}