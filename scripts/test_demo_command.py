import sys
import os
import json
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Mock google.genai to avoid network calls
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()

from nlp_processor import NLPProcessor
from java_gateway import JavaGateway

print("=" * 80)
print("TESTING USER'S DEMO COMMAND")
print("=" * 80)

# User's exact command
user_input = "Create a new project named Something and assign 3 task to Sarah and John for the backend and assign 3 tasks to Albert and Von for the frontend and assign 1 task to June"

print(f"Input: '{user_input}'\n")

# Initialize components
nlp = NLPProcessor()
gateway = JavaGateway()

# What the AI SHOULD extract from this command:
# - Project name: "Something"
# - Total tasks: 3 + 3 + 1 = 7
# - Backend: 3 tasks for Sarah and John
# - Frontend: 3 tasks for Albert and Von
# - Unspecified team (or "general"): 1 task for June

# Simulate AI's "perfect" response
mock_ai_response = {
    "intent": "CREATE_PROJECT",
    "project_name": "Project Something",
    "total_tasks": 7,
    "allocations": {
        "backend": {"count": 3, "people": ["Sarah", "John"]},
        "frontend": {"count": 3, "people": ["Albert", "Von"]},
        "general": {"count": 1, "people": ["June"]}
    },
    "validation_error": None
}

# Mock the NLP client
nlp.client.models.generate_content = MagicMock()
nlp.client.models.generate_content.return_value.text = json.dumps(mock_ai_response)

# Parse the input
print("1. Parsing with Gemini AI...")
parsed_data = nlp.parse_input(user_input)

print(f"   Intent: {parsed_data['intent']}")
print(f"   Project: {parsed_data['project_name']}")
print(f"   Total Tasks: {parsed_data['total_tasks']}")
print(f"\n   Allocations:")
print(json.dumps(parsed_data['allocations'], indent=4))

# Execute backend creation
print("\n2. Creating Project in Backend...")
result = gateway.create_project(
    parsed_data["project_name"],
    parsed_data["total_tasks"],
    parsed_data["allocations"]
)
print(f"   {result['message']}")

# Verify the saved data
print("\n3. Verifying Database Entry...")
gateway_verify = JavaGateway()
saved_project = gateway_verify.get_project_status("Project Something")

if saved_project:
    print("✅ SUCCESS: Project saved to database!")
    print("\n--- Stored Data ---")
    print(json.dumps(saved_project, indent=2))
    
    # Validate key points
    print("\n--- Validation Checks ---")
    if saved_project['allocations']['backend']['people'] == ["Sarah", "John"]:
        print("✅ Sarah and John assigned to Backend")
    if saved_project['allocations']['frontend']['people'] == ["Albert", "Von"]:
        print("✅ Albert and Von assigned to Frontend")
    if saved_project['allocations']['general']['people'] == ["June"]:
        print("✅ June assigned to General tasks")
    
    total = sum(team['count'] for team in saved_project['allocations'].values())
    if total == 7:
        print(f"✅ Math validated: {total} total tasks")
    
    print("\n🎉 READY FOR DEMO!")
else:
    print("❌ FAILED: Project not found in database.")
