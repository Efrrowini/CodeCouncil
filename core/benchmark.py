import json
import time
from core.baseline import single_agent_review
from core.debate import run_debate

TEST_CASES = [
    {
        "name": "SQL Injection + Hardcoded Secret",
        "diff": """
diff --git a/app/users.py b/app/users.py
@@ -10,6 +10,15 @@
+def get_user(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    result = db.execute(query)
+    password = result['password']
+    return result
+
+API_KEY = "sk-1234567890abcdef"
""",
        "expected_issues": ["sql injection", "hardcoded", "password exposure"],
        "expected_verdict": "BLOCK"
    },
    {
        "name": "N+1 Query + Missing Error Handling",
        "diff": """
diff --git a/app/orders.py b/app/orders.py
@@ -5,6 +5,14 @@
+def get_all_orders(users):
+    orders = []
+    for user in users:
+        user_orders = db.query(f"SELECT * FROM orders WHERE user_id={user.id}")
+        orders.extend(user_orders)
+    return orders
+
+def process_payment(amount):
+    result = payment_gateway.charge(amount)
+    return result
""",
        "expected_issues": ["n+1", "error handling", "sql injection"],
        "expected_verdict": "BLOCK"
    },
    {
        "name": "Clean Code — Poor Naming + No Tests",
        "diff": """
diff --git a/app/utils.py b/app/utils.py
@@ -1,6 +1,18 @@
+def p(x, y, z):
+    if x == 1:
+        return y * z
+    elif x == 2:
+        return y + z
+    elif x == 3:
+        return y - z
+    else:
+        return 0
+
+def calc(a, b, c, d, e, f, g):
+    t = p(a, b, c)
+    r = p(d, e, f)
+    return t + r + g
""",
        "expected_issues": ["naming", "readability", "no tests"],
        "expected_verdict": "REQUEST_CHANGES"
    }
]


def score_issues(found_issues: list, expected_keywords: list) -> float:
    if not expected_keywords:
        return 1.0
    found_text = " ".join([
        (i.get("description", "") + " " + i.get("category", "")).lower()
        for i in found_issues
    ])
    hits = sum(1 for kw in expected_keywords if kw.lower() in found_text)
    return hits / len(expected_keywords)


def get_issue_categories(issues: list) -> set:
    cats = set()
    for i in issues:
        cat = i.get("category", "").lower()
        desc = i.get("description", "").lower()
        if cat == "security" or any(w in desc for w in ["injection", "secret", "xss", "auth", "password"]):
            cats.add("security")
        if cat == "performance" or any(w in desc for w in ["n+1", "loop", "query", "complexity", "memory"]):
            cats.add("performance")
        if cat == "quality" or any(w in desc for w in ["naming", "readability", "solid", "test", "duplicate"]):
            cats.add("quality")
    return cats


def run_benchmark():
    print("\n" + "="*60)
    print("CODECOUNCIL BENCHMARK: Multi-Agent vs Single-Agent")
    print("="*60)

    results = []

    for i, case in enumerate(TEST_CASES):
        print(f"\n📋 Test Case {i+1}: {case['name']}")
        print("-" * 40)

        print("  Running single-agent baseline...")
        t0 = time.time()
        baseline = single_agent_review(case["diff"])
        baseline_time = time.time() - t0

        print("  Running multi-agent debate...")
        t0 = time.time()
        council = run_debate(case["diff"])
        council_time = time.time() - t0

        baseline_issues = baseline.get("issues", [])

        council_all_issues = []
        for agent in council.get("round1", []):
            council_all_issues.extend(agent.get("issues", []))
        council_issues = council_all_issues

        baseline_score = score_issues(baseline_issues, case["expected_issues"])
        council_score = score_issues(council_issues, case["expected_issues"])

        baseline_cats = get_issue_categories(baseline_issues)
        council_cats = get_issue_categories(council_issues)

        baseline_verdict_correct = baseline.get("verdict") == case["expected_verdict"]
        council_verdict_correct = council.get("final", {}).get("final_verdict") == case["expected_verdict"]

        result = {
            "case": case["name"],
            "baseline": {
                "issues_found": len(baseline_issues),
                "detection_score": round(baseline_score * 100),
                "verdict": baseline.get("verdict"),
                "verdict_correct": baseline_verdict_correct,
                "confidence": baseline.get("confidence", 0),
                "categories_covered": list(baseline_cats),
                "time_seconds": round(baseline_time, 1)
            },
            "council": {
                "issues_found": len(council_issues),
                "detection_score": round(council_score * 100),
                "verdict": council.get("final", {}).get("final_verdict"),
                "verdict_correct": council_verdict_correct,
                "confidence": council.get("final", {}).get("confidence", 0),
                "categories_covered": list(council_cats),
                "time_seconds": round(council_time, 1),
                "debate_rounds": 3
            }
        }
        results.append(result)

        print(f"\n  SINGLE AGENT:")
        print(f"    Issues found:      {result['baseline']['issues_found']}")
        print(f"    Detection score:   {result['baseline']['detection_score']}%")
        print(f"    Verdict:           {result['baseline']['verdict']} ({'✓' if baseline_verdict_correct else '✗'})")
        print(f"    Confidence:        {result['baseline']['confidence']}%")
        print(f"    Categories:        {result['baseline']['categories_covered']}")
        print(f"    Time:              {result['baseline']['time_seconds']}s")

        print(f"\n  CODECOUNCIL (Multi-Agent):")
        print(f"    Issues found:      {result['council']['issues_found']}")
        print(f"    Detection score:   {result['council']['detection_score']}%")
        print(f"    Verdict:           {result['council']['verdict']} ({'✓' if council_verdict_correct else '✗'})")
        print(f"    Confidence:        {result['council']['confidence']}%")
        print(f"    Categories:        {result['council']['categories_covered']}")
        print(f"    Time:              {result['council']['time_seconds']}s")

    print("\n" + "="*60)
    print("AGGREGATE RESULTS")
    print("="*60)

    avg_baseline_detection = sum(r["baseline"]["detection_score"] for r in results) / len(results)
    avg_council_detection = sum(r["council"]["detection_score"] for r in results) / len(results)
    baseline_verdicts = sum(1 for r in results if r["baseline"]["verdict_correct"])
    council_verdicts = sum(1 for r in results if r["council"]["verdict_correct"])
    avg_baseline_conf = sum(r["baseline"]["confidence"] for r in results) / len(results)
    avg_council_conf = sum(r["council"]["confidence"] for r in results) / len(results)

    improvement = avg_council_detection - avg_baseline_detection
    verdict_improvement = council_verdicts - baseline_verdicts

    print(f"\n  Detection Score:   Baseline {avg_baseline_detection:.0f}%  ->  CodeCouncil {avg_council_detection:.0f}%  ({improvement:+.0f}%)")
    print(f"  Verdict Accuracy:  Baseline {baseline_verdicts}/{len(results)}  ->  CodeCouncil {council_verdicts}/{len(results)}")
    print(f"  Avg Confidence:    Baseline {avg_baseline_conf:.0f}%  ->  CodeCouncil {avg_council_conf:.0f}%")
    print(f"\n  CodeCouncil improvement: {improvement:+.0f}% detection, {verdict_improvement:+d} verdict accuracy")

    with open("benchmark_results.json", "w") as f:
        json.dump({
            "summary": {
                "baseline_detection": round(avg_baseline_detection),
                "council_detection": round(avg_council_detection),
                "improvement_percent": round(improvement),
                "baseline_verdict_accuracy": f"{baseline_verdicts}/{len(results)}",
                "council_verdict_accuracy": f"{council_verdicts}/{len(results)}",
            },
            "cases": results
        }, f, indent=2)

    print(f"\n  Results saved to benchmark_results.json")
    print("="*60)


if __name__ == "__main__":
    run_benchmark()
    {
        "name": "Subtle Auth Bypass — Debate Catches It",
        "diff": """
diff --git a/app/auth.py b/app/auth.py
@@ -5,6 +5,16 @@
+def verify_user(user_id, token):
+    user = db.get(user_id)
+    if user.token == token:
+        return True
+    return False
+
+def reset_password(user_id, new_password):
+    user = db.get(user_id)
+    user.password = new_password
+    db.save(user)
+    return True
""",
        "expected_issues": ["timing attack", "no authorization", "plaintext password"],
        "expected_verdict": "BLOCK"
    },