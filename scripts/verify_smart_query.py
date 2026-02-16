import json
import os
import sys

# Inject Risky Data
db_file = "projects.json"
projects = {}

if os.path.exists(db_file):
    with open(db_file, "r") as f:
        projects = json.load(f)

projects["Project Risky"] = {
    "status": "In Progress",
    "completion": 30,
    "delayed_tasks": 5,
    "total_tasks": 10
}

with open(db_file, "w") as f:
    json.dump(projects, f, indent=2)

print("✅ Injected 'Project Risky' into database.")

# Now verify the response
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from nlp_processor import NLPProcessor
from unittest.mock import MagicMock

# Attempt to Use Real API (if quota available) or Mock it to simulate "Smartness"
# Since we can't guarantee quota, I will mock the LLM response to prove the PROMPT is correct.

nlp = NLPProcessor()
print("\n--- Testing Smart Response Prompt Construction ---")

# Mock the generate_content to print the prompt it received
original_generate = nlp.client.models.generate_content
nlp.client.models.generate_content = MagicMock()
nlp.client.models.generate_content.return_value.text = "Mocked Risk Analysis: Project is at risk due to delays."

data = {
    "intent": "GET_STATUS",
    "project_name": "Project Risky",
    "project_data": projects["Project Risky"]
}

nlp.generate_smart_response(data)

# Check what was sent to the LLM
kwargs = nlp.client.models.generate_content.call_args.kwargs
actual_prompt = kwargs['contents']

print("\n[ACTUAL PROMPT SENT TO AI]:")
print(actual_prompt)

if "CRITICAL INSTRUCTIONS" in actual_prompt and "If 'delayed_tasks' > 0, flag this as a RISK" in actual_prompt:
    print("\n✅ SUCCESS: The system is now sending Risk Analysis instructions to the AI.")
else:
    print("\n❌ FAILURE: Prompt does not contain risk instructions.")
