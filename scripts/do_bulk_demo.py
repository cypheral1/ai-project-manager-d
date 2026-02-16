import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Mock google.genai BEFORE importing nlp_processor to avoid network
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()

from nlp_processor import NLPProcessor
from java_gateway import JavaGateway

print("=" * 80)
print("EXECUTING BULK ACTION ENGINE (End-to-End)")
print("=" * 80)

# Patch the Client inside NLPProcessor
with patch('nlp_processor.genai.Client') as MockClient:
    # 1. Setup Components
    nlp = NLPProcessor()
    gateway = JavaGateway()
    
    # 2. Define the User Input
    user_input = "Create Project Gamma with 16 tasks, assign 7 to frontend (John, Sarah), 5 to backend (Mike, Tom), 4 to testing (Lisa)"
    print(f"User Input: '{user_input}'\n")

    # 3. Simulate the AI's "Brain" (The Perfect Parse)
    # This is what Gemini WOULD return given our prompt.
    mock_ai_response = {
        "intent": "CREATE_PROJECT",
        "project_name": "Project Gamma",
        "total_tasks": 16,
        "allocations": {
            "frontend": {"count": 7, "people": ["John", "Sarah"]},
            "backend": {"count": 5, "people": ["Mike", "Tom"]},
            "testing": {"count": 4, "people": ["Lisa"]}
        },
        "validation_error": None
    }
    
    # Configure Mock
    mock_instance = MockClient.return_value
    mock_instance.models.generate_content.return_value.text = json.dumps(mock_ai_response)
    
    # 4. Run the Parsing Logic
    print("1. Parsing with NLP Module...")
    parsed_data = nlp.parse_input(user_input)
    print(f"   Parsed Intent: {parsed_data['intent']}")
    print(f"   Structure: {json.dumps(parsed_data['allocations'], indent=2)}")

    # 5. Execute Backend Action
    print("\n2. Executing Java Backend...")
    if parsed_data["intent"] == "CREATE_PROJECT":
        result = gateway.create_project(
            parsed_data["project_name"],
            parsed_data["total_tasks"],
            parsed_data["allocations"]
        )
        print(f"   Result: {result['message']}")

    # 6. Verify Persistence
    print("\n3. Verifying Database (projects.json)...")
    
    # Reload gateway data to ensure it reads from disk
    gateway_verify = JavaGateway()
    saved_project = gateway_verify.get_project_status("Project Gamma")
    
    if saved_project:
        print(f"✅ SUCCESS: Project Gamma saved to disk.")
        print(json.dumps(saved_project, indent=2))
        
        # Check specific data points
        print("\n--- Validation ---")
        fe_people = saved_project['allocations']['frontend']['people']
        if "John" in fe_people and "Sarah" in fe_people:
            print("✅ 'John' and 'Sarah' assigned to Frontend.")
        else:
            print("❌ Assignment Failed.")
            
    else:
        print("❌ FAILED: Project Gamma not found in DB.")
