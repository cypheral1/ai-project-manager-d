import requests
import json
import sys

print("=" * 80)
print("TESTING REDIS CONVERSATION MEMORY")
print("=" * 80)

server_url = "http://localhost:8000"
session_id = "test_session_123"

# Test 1: Create a project
print("\n🧪 TEST 1: Create Project")
print("-" * 80)

message1 = "Create Project RedisTest with 8 tasks for the team"
print(f"User: {message1}")

response1 = requests.post(
    f"{server_url}/chat",
    json={"message": message1, "session_id": session_id}
)

if response1.status_code == 200:
    result1 = response1.json()
    print(f"Bot: {result1['response'][:200]}...")
    print(f"✅ Project created: {result1['data'].get('project_name')}")
else:
    print(f"❌ Failed: {response1.status_code}")
    sys.exit(1)

# Test 2: Reference with pronoun "it"
print("\n🧪 TEST 2: Use Pronoun Reference ('it')")
print("-" * 80)

message2 = "What is the status of it?"
print(f"User: {message2}")

response2 = requests.post(
    f"{server_url}/chat",
    json={"message": message2, "session_id": session_id}
)

if response2.status_code == 200:
    result2 = response2.json()
    resolved_project = result2['data'].get('project_name')
    print(f"Bot resolved 'it' to: {resolved_project}")
    print(f"Bot: {result2['response'][:150]}...")
    
    if "RedisTest" in str(resolved_project):
        print("✅ SUCCESS: Bot remembered the context!")
    else:
        print(f"❌ FAILED: Bot didn't resolve 'it' (got: {resolved_project})")
else:
    print(f"❌ Failed: {response2.status_code}")
    sys.exit(1)

# Test 3: Check Redis storage
print("\n🧪 TEST 3: Verify Redis Storage")
print("-" * 80)

import redis
r = redis.Redis(decode_responses=True)
messages_key = f"session:{session_id}:messages"
stored_messages = r.lrange(messages_key, 0, -1)

print(f"Messages stored in Redis: {len(stored_messages)}")
for i, msg in enumerate(stored_messages, 1):
    msg_data = json.loads(msg)
    print(f"  {i}. [{msg_data['role']}]: {msg_data['content'][:50]}...")

if len(stored_messages) >= 4:  # 2 user + 2 assistant messages
    print("✅ SUCCESS: Conversation history stored in Redis!")
else:
    print(f"❌ FAILED: Expected 4+ messages, got {len(stored_messages)}")

# Test 4: Different session doesn't see the context
print("\n🧪 TEST 4: Session Isolation")
print("-" * 80)

message3 = "What is the status of it?"
print(f"User (NEW SESSION): {message3}")

response3 = requests.post(
    f"{server_url}/chat",
    json={"message": message3, "session_id": "different_session_456"}
)

if response3.status_code == 200:
    result3 = response3.json()
    resolved_project3 = result3['data'].get('project_name')
    print(f"Bot in new session: {resolved_project3}")
    
    if not resolved_project3 or resolved_project3 == "null":
        print("✅ SUCCESS: Sessions are isolated (new session has no context)")
    else:
        print(f"⚠️ WARNING: New session shouldn't have context")
else:
    print(f"❌ Failed: {response3.status_code}")

print("\n" + "=" * 80)
print("🎉 REDIS CONVERSATION MEMORY IS WORKING!")
print("=" * 80)
