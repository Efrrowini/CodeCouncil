import json, os, traceback
from core.debate import run_debate

diff = """+def get_user(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return db.execute(query)
+API_KEY = "sk-1234567890"
"""

try:
    print("Starting debate...")
    result = run_debate(diff, repo="Efrrowini/codecouncil-test")
    print("Debate done.")
    print("CONFLICTS:", len(result.get("conflicts", [])))
    print("CALIBRATION:", len(result.get("calibration", [])))
    print("DEBATE IMPACT:", result.get("debate_impact", {}))
    print("MEMORY FILE CREATED:", os.path.exists("pr_memory.json"))
except Exception as e:
    print("ERROR:", e)
    traceback.print_exc()