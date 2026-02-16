import sys
import os
import json
import spacy
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Mock google.genai if needed, but we want to test the spaCy part mainly
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()

from nlp_processor import NLPProcessor

def verify_spacy():
    print("=" * 80)
    print("VERIFYING SPACY INTEGRATION")
    print("=" * 80)

    try:
        nlp_proc = NLPProcessor()
        if nlp_proc.nlp:
            print("✅ spaCy Initialized Successfully")
        else:
            print("❌ spaCy Failed to Initialize")
            return
    except Exception as e:
        print(f"❌ Error during init: {e}")
        return

    # Simulate Rate Limit to force Local Parser + spaCy
    nlp_proc.client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED")

    user_input = "Assign 3 tasks to John and Sarah for Project Omega by next Friday"
    print(f"\nInput: '{user_input}'")

    result = nlp_proc.parse_input(user_input)
    print(f"Output: {json.dumps(result, indent=2)}")

    entities = result.get("entities", {})
    people = entities.get("people", [])
    dates = entities.get("dates", [])

    if "John" in people and "Sarah" in people:
        print("✅ ENTITIES FOUND: People extracted correctly!")
    else:
        print("❌ ENTITIES MISSING: People not found.")

    if dates:
         print(f"✅ DATES FOUND: {dates}")

if __name__ == "__main__":
    verify_spacy()
