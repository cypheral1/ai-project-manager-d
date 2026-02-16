import sys
import os
import json

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from nlp_processor import NLPProcessor
from java_gateway import JavaGateway

def do_project_b():
    print("=" * 80)
    print("EXECUTING USER REQUEST: Project B")
    print("=" * 80)

    nlp = NLPProcessor()
    gateway = JavaGateway()

    # User's exact prompt
    user_input = "Create a project named B and assign 2 task to the backend team 2 to the frontend team"
    print(f"Input: '{user_input}'")

    print("\n1. Parsing Input...")
    parsed_data = nlp.parse_input(user_input)
    print(f"   Parsed Data: {json.dumps(parsed_data, indent=2)}")

    if parsed_data.get("intent") == "CREATE_PROJECT":
        print("\n2. Executing Backend Creation...")
        result = gateway.create_project(
            parsed_data["project_name"],
            parsed_data["total_tasks"],
            parsed_data["allocations"]
        )
        print(f"   Backend Response: {result}")
        
        if result["success"]:
             print(f"\n✅ RESULT: {result['message']}")
             
             # --- Now Check Status ---
             print("\n3. Verifying Status Retrieval...")
             status_input = "Status of Project B"
             print(f"   Input: '{status_input}'")
             
             parsed_status = nlp.parse_input(status_input)
             if parsed_status.get("project_name") == "Project B":
                 status_data = gateway.get_project_status("Project B")
                 print(f"   ✅ STATUS FOUND: {json.dumps(status_data, indent=2)}")
             else:
                 print(f"   ❌ FAILED: Parser didn't find Project B in status request.")
                 
        else:
             print(f"\n❌ FAILED: {result['message']}")
    else:
        print(f"\n❌ FAILED: Could not understand intent. Data: {parsed_data}")

if __name__ == "__main__":
    do_project_b()
