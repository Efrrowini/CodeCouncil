import json
from core.debate import run_debate

TEST_DIFF = """
diff --git a/app/users.py b/app/users.py
@@ -10,6 +10,20 @@
+def get_user(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    result = db.execute(query)
+    password = result['password']
+    return result
+
+def process_users(users):
+    result = []
+    for user in users:
+        for order in db.execute(f"SELECT * FROM orders WHERE user_id = {user['id']}"):
+            result.append(order)
+    return result
+
+API_KEY = "sk-1234567890abcdef"
"""

print("Starting full debate...\n")
result = run_debate(TEST_DIFF)

print("\n=== ROUND 1 SUMMARY ===")
for agent in result["round1"]:
    print(f"{agent.get('agent')}: {agent.get('verdict')} (confidence: {agent.get('confidence')}%)")

print("\n=== ROUND 2 DEBATE ===")
for agent in result["round2"]:
    name = agent.get("agent")
    agreements = agent.get("agreements", [])
    disagreements = agent.get("disagreements", [])
    print(f"\n{name}:")
    print(f"  Agrees with: {[a['with_agent'] for a in agreements]}")
    print(f"  Disagrees with: {[d['with_agent'] for d in disagreements]}")
    print(f"  Updated verdict: {agent.get('updated_verdict')} ({agent.get('updated_confidence')}%)")

print("\n=== FINAL VERDICT ===")
final = result["final"]
print(json.dumps(final, indent=2))