import sys
import os
import json
import requests
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from java_gateway import JavaGateway
from nlp_processor import NLPProcessor

print("=" * 80)
print("VERIFYING DETERMINISTIC RISK ENGINE")
print("=" * 80)

# 1. Setup Data
gateway = JavaGateway()
gateway.projects["Project Risky"] = {
    "status": "In Progress",
    "completion": 15, 
    "delayed_tasks": 4, 
    "total_tasks": 10
}
gateway.save_data()

# 2. Test Gateway Logic Directly
print("\n--- Testing Gateway Logic ---")
risk = gateway.analyze_project_risk("Project Risky")
print(f"Risk Output: {json.dumps(risk, indent=2)}")

if risk["risk_score"] >= 60 and risk["risk_level"] == "HIGH":
    print("✅ Gateway Logic Correct: High Risk identified.")
else:
    print("❌ Gateway Logic Failed.")

# 3. Test Full Flow (Mocked API)
print("\n--- Testing NLP Integration ---")
nlp = NLPProcessor()
nlp.client.models.generate_content = MagicMock()
nlp.client.models.generate_content.return_value.text = "Mocked Response: Risk is High."

data = {
    "intent": "GET_STATUS",
    "project_name": "Project Risky",
    "project_data": gateway.get_project_status("Project Risky"),
    "risk_analysis": risk  # This is what main.py injects
}

# Generate Prompt
nlp.generate_smart_response(data)
kwargs = nlp.client.models.generate_content.call_args.kwargs
actual_prompt = kwargs['contents']

print(f"\n[PROMPT WITH RISK DATA]:\n{actual_prompt}")

if "risk_score" in actual_prompt and "delayed tasks" in actual_prompt:
     print("✅ NLP received the structured Risk Data.")
else:
     print("❌ NLP did not receive risk data.")
