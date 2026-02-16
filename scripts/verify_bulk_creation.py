import sys
import os
import json
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from unittest.mock import patch, MagicMock
from nlp_processor import NLPProcessor

print("=" * 80)
print("VERIFYING BULK ACTION PARSING")
print("=" * 80)

# Patch the Client creation to avoid network calls
with patch('google.genai.Client') as MockClient:
    nlp = NLPProcessor()
    
    # Configure the mock client instance
    mock_instance = MockClient.return_value
    mock_models = mock_instance.models
    mock_generate = mock_models.generate_content
    
    # Mock Response
    mock_json = {
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
    mock_generate.return_value.text = json.dumps(mock_json)

    # Complex Prompt from memory.txt
    user_input = "Create Project Gamma with 16 tasks, assign 7 to frontend (John, Sarah), 5 to backend (Mike, Tom), 4 to testing (Lisa)"
    print(f"Input: '{user_input}'")

    nlp.parse_input(user_input)
    
    # Get the actual prompt passed to generate_content
    kwargs = mock_generate.call_args.kwargs
    actual_prompt = kwargs['contents']

    print(f"[PROMPT]:\n{actual_prompt}")

    if "people" in actual_prompt:
        print("\n✅ Prompt ALREADY asks for people.")
    else:
        print("\n❌ Prompt DOES NOT ask for people. Update needed.")
