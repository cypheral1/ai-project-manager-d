import requests
import json
import time

print("=" * 80)
print("TESTING WITH REAL API (FastAPI + Real Gemini)")
print("=" * 80)

# Server is already running
server_url = "http://localhost:8000"

# User's exact command
user_message = "Create a new project named Something and assign 3 task to Sarah and John for the backend and assign 3 tasks to Albert and Von for the frontend and assign 1 task to June"

print(f"\nUser Command:\n'{user_message}'\n")
print("Sending to REAL FastAPI server (using REAL Gemini API)...\n")

# Send real HTTP request
try:
    response = requests.post(
        f"{server_url}/chat",
        json={"message": user_message},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("=" * 80)
        print("✅ REAL API RESPONSE")
        print("=" * 80)
        
        print(f"\n📊 Intent Detected: {result.get('intent')}")
        
        print(f"\n💬 AI's Natural Language Response:")
        print(f"   \"{result.get('response')}\"\n")
        
        print("📋 Structured Data Extracted by AI:")
        data = result.get('data', {})
        print(f"   • Project: {data.get('project_name')}")
        print(f"   • Total Tasks: {data.get('total_tasks')}")
        
        if 'allocations' in data and data['allocations']:
            print("\n   • Team Assignments:")
            for team, details in data['allocations'].items():
                if isinstance(details, dict) and 'people' in details:
                    people_str = ", ".join(details['people'])
                    print(f"      - {team.title()}: {details['count']} tasks → {people_str}")
        
        # Verify database
        print("\n" + "=" * 80)
        print("📁 DATABASE VERIFICATION")
        print("=" * 80)
        
        with open('/home/sairaj-s-den/FEDI/projects.json', 'r') as f:
            projects = json.load(f)
        
        if "Project Something" in projects:
            print("✅ Project 'Something' successfully saved to database!\n")
            project_data = projects["Project Something"]
            print(f"   Status: {project_data['status']}")
            print(f"   Total Tasks: {project_data['total_tasks']}")
            print(f"   Completion: {project_data['completion']}%")
            
            print("\n   Stored Allocations:")
            print(json.dumps(project_data['allocations'], indent=6))
            
            print("\n🎉 SUCCESS: Your demo command works with the REAL AI!")
        else:
            print("⚠️ Project not found in database.")
            print(f"   Available projects: {list(projects.keys())}")
            
    else:
        print(f"❌ Request failed with status: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error communicating with server: {e}")
    print("\nMake sure the FastAPI server is running:")
    print("   cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000")
