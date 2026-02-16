import json
import os
import sys
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from nlp_processor import NLPProcessor

print("=" * 80)
print("VERIFYING SMART QUERY FALLBACK")
print("=" * 80)

nlp = NLPProcessor()

# Inject Risky Data Mock
project_data = {
    "status": "In Progress",
    "completion": 30,
    "delayed_tasks": 5,
    "total_tasks": 10
}
data = {
    "intent": "GET_STATUS",
    "project_name": "Project Risky",
    "project_data": project_data,
    "risk_analysis": {
        "risk_score": 60,
        "risk_level": "HIGH",
        "risk_factors": ["4 delayed tasks", "Low completion rate"]
    }
}

# FORCE API FAILURE
nlp.client.models.generate_content = MagicMock(side_effect=Exception("429 RESOURCE_EXHAUSTED"))

print("\n1. Generating Response (API DOWN)...")
response = nlp.generate_smart_response(data)
print(f"   Output: {response}")

if "CRITICAL RISK DETECTED" in response and "4 delayed tasks" in response:
    print("✅ SUCCESS: Local fallback identified the risk!")
else:
    print("❌ FAILED: Local fallback missed the risk.")
