import requests
import json
import time
import subprocess
import sys
import os

print("=" * 80)
print("TESTING WITH REAL API (FastAPI + Real Gemini)")
print("=" * 80)

# Check if server is running
server_url = "http://localhost:8000"
server_running = False

try:
    response = requests.get(f"{server_url}/health", timeout=2)
    if response.status_code == 200:
        server_running = True
        print("✅ Server is already running.")
except:
    print("⚠️ Server not running. Starting it now...")

# Start server if not running
server_process = None
if not server_running:
    # Start the FastAPI server in the background
    server_process = subprocess.Popen(
        ["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd="/home/sairaj-s-den/FEDI",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("   Waiting for server to start...")
    time.sleep(3)  # Give it time to start
    
    # Verify it started
    try:
        response = requests.get(f"{server_url}/health", timeout=2)
        if response.status_code == 200:
            print("   ✅ Server started successfully!")
        else:
            print("   ❌ Server failed to start.")
            sys.exit(1)
    except Exception as e:
        print(f"   ❌ Server failed to start: {e}")
        sys.exit(1)

# User's exact command
user_message = "Create a new project named Something and assign 3 task to Sarah and John for the backend and assign 3 tasks to Albert and Von for the frontend and assign 1 task to June"

print(f"\nUser Command: '{user_message}'\n")
print("Sending to REAL API (Gemini will process this)...")

# Send real HTTP request to the FastAPI server
try:
    response = requests.post(
        f"{server_url}/chat",
        json={"message": user_message},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n" + "=" * 80)
        print("REAL API RESPONSE")
        print("=" * 80)
        
        print(f"\n📊 Intent: {result.get('intent')}")
        print(f"\n💬 AI Response:\n   {result.get('response')}\n")
        
        print("📋 Parsed Data:")
        data = result.get('data', {})
        print(f"   Project: {data.get('project_name')}")
        print(f"   Total Tasks: {data.get('total_tasks')}")
        
        if 'allocations' in data:
            print("\n   Allocations:")
            print(json.dumps(data['allocations'], indent=6))
        
        # Check if it was created in the database
        print("\n" + "=" * 80)
        print("VERIFYING DATABASE")
        print("=" * 80)
        
        # Read projects.json
        with open('/home/sairaj-s-den/FEDI/projects.json', 'r') as f:
            projects = json.load(f)
        
        if "Project Something" in projects:
            print("✅ Project 'Something' found in database!")
            print(json.dumps(projects["Project Something"], indent=2))
        else:
            print("⚠️ Project not found in database yet.")
            
    else:
        print(f"❌ Request failed with status: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")

finally:
    # Clean up: kill the server if we started it
    if server_process:
        print("\n⚠️ Stopping test server...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("   Server stopped.")
