import sys
import os
import json
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# MOCK the genai module before importing nlp_processor
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()

from nlp_processor import NLPProcessor

def verify_hybrid_mode():
    print("=" * 80)
    print("VERIFYING HYBRID MODE (Regex Fallback)")
    print("=" * 80)

    nlp = NLPProcessor()

    # FORCE the API to FAIL with Rate Limit
    nlp.client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED")

    # --- SCENARIO 1: CREATE PROJECT ---
    print("\n🔹 SCENARIO 1: Create Project (API DOWN)")
    user_input = "Create Project Omega with 5 tasks"
    print(f"   Input: '{user_input}'")
    
    result = nlp.parse_input(user_input)
    print(f"   Output: {json.dumps(result, indent=2)}")

    if result.get("project_name") == "Project Omega" and result.get("total_tasks") == 5:
        print("   ✅ SUCCESS: Local parser took over correctly!")
    else:
        print("   ❌ FAILED: Did not parse correctly.")

    # --- SCENARIO 2: STATUS CHECK ---
    print("\n🔹 SCENARIO 2: Status Check (API DOWN)")
    user_input = "Status of Project Omega"
    print(f"   Input: '{user_input}'")

    result = nlp.parse_input(user_input)
    print(f"   Output: {json.dumps(result, indent=2)}")

    if result.get("intent") == "GET_STATUS" and result.get("project_name") == "Project Omega":
        print("   ✅ SUCCESS: Local parser took over correctly!")
    else:
        print("   ❌ FAILED: Did not parse correctly.")

if __name__ == "__main__":
    verify_hybrid_mode()
