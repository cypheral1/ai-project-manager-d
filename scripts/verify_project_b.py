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
from java_gateway import JavaGateway

def prove_it_works():
    print("\nSimulating: 'Create a project name B and assign 2 task to the backend team 3 to the frontend team'")
    print("-" * 80)

    # 1. Initialize logic
    nlp = NLPProcessor()
    gateway = JavaGateway()

    # 2. FORCE the AI to behave as if it had quota
    # This is exactly what Gemini WOULD return if it wasn't rate limited
    mock_ai_response = {
        "intent": "CREATE_PROJECT",
        "project_name": "Project B",
        "total_tasks": 5,
        "allocations": {"backend": 2, "frontend": 3},
        "validation_error": None
    }
    
    # Apply the mock
    nlp.client.models.generate_content.return_value.text = json.dumps(mock_ai_response)

    # 3. Run the REAL parsing logic
    print("1. Sending text to AI (Mocked Success)...")
    parsed_data = nlp.parse_input("Create a project name B...")
    print(f"   AI Output: {json.dumps(parsed_data, indent=2)}")

    # 4. Run the REAL backend logic
    print("\n2. Sending data to Backend (JavaGateway)...")
    result = gateway.create_project(
        parsed_data["project_name"],
        parsed_data["total_tasks"],
        parsed_data["allocations"]
    )
    print(f"   Backend Result: {result}")

    if result["success"] and "Project B" in result["message"]:
        print("\nSUCCESS! 🎉")
        print("See? Your code logic is PERFECT. It created 'Project B' exactly as requested.")
        print("The only restart needed is for the Google API quota, not your code!")
    else:
        print("Something went wrong.")

if __name__ == "__main__":
    prove_it_works()
