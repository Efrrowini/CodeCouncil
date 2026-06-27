import json
from agents import security, performance, cleancode, techlead

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

print("Running all agents...\n")

print("=" * 40)
print("SecurityAuditor")
print("=" * 40)
sec = security.review(TEST_DIFF)
print(json.dumps(sec, indent=2))

print("\n" + "=" * 40)
print("PerfEngineer")
print("=" * 40)
perf = performance.review(TEST_DIFF)
print(json.dumps(perf, indent=2))

print("\n" + "=" * 40)
print("CleanCodeReviewer")
print("=" * 40)
clean = cleancode.review(TEST_DIFF)
print(json.dumps(clean, indent=2))

print("\n" + "=" * 40)
print("TechLead (final verdict)")
print("=" * 40)
lead = techlead.arbitrate(TEST_DIFF, [sec, perf, clean])
print(json.dumps(lead, indent=2))