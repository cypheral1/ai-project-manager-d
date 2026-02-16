from google import genai
import os
import json
from dotenv import load_dotenv
import spacy

load_dotenv()

class NLPProcessor:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        self.client = genai.Client(api_key=api_key)
        
        # Initialize spaCy
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("DEBUG: spaCy model loaded successfully.")
        except OSError:
            print("WARNING: spaCy model 'en_core_web_sm' not found. Entity extraction will be limited.")
            self.nlp = None

    def parse_input(self, user_input: str) -> dict:
        """
        Uses Gemini to parse the user input into a structured JSON 
        containing intent, entities, and validation checks.
        """
        
        prompt = f"""
        You are a project management command parser. 
        Analyze the following user input and return a strictly valid JSON (no markdown).

        User Input: "{user_input}"

        Identify the intent:
        - "GET_STATUS": asking about project progress, status, or updates.
        - "CREATE_PROJECT": asking to create a new project, add tasks, or assign work.
        - "UNKNOWN": if it doesn't fit the above.

        Extraction Rules:
        1. "project_name": Extract the project name (digits allowed).
        2. "total_tasks": Valid integer of total tasks mentioned.
        3. "allocations": For CREATE_PROJECT, extract specific team assignments.
           - Format: {{ "team_name": {{ "count": int, "people": ["Name1", "Name2"] }} }}
           - If no people mentioned, "people" should be empty list [].
           - "team_name" should be normalized (frontend, backend, testing, design, etc.).
        4. "validation_error": If the sum of allocations (counts) does not match total_tasks (only if all are present), indicate the error message. Otherwise null.

        Output Format:
        {{
            "intent": "GET_STATUS" | "CREATE_PROJECT" | "UNKNOWN",
            "project_name": "extracted name" or null,
            "total_tasks": 0 or null,
            "allocations": {{ 
                "frontend": {{ "count": 0, "people": [] }}, 
                "backend": {{ "count": 0, "people": [] }},
                ...
            }} or {{}},
            "validation_error": "error string" or null
        }}
        """

        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
        import time

        def is_rate_limit_error(exception):
            return "429" in str(exception) or "RESOURCE_EXHAUSTED" in str(exception)

        @retry(
            retry=retry_if_exception(is_rate_limit_error),
            stop=stop_after_attempt(1),
            wait=wait_exponential(multiplier=1, min=1, max=5)
        )
        def call_gemini():
            print(f"DEBUG: Processing input: {user_input}")
            return self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

        try:
            response = call_gemini()
            
            # Clean up potential markdown code blocks provided by the model
            raw_text = response.text.strip()
            print(f"DEBUG: Raw Gemini response: {raw_text}")
            
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            # Enrich with spaCy entities (if available)
            parsed_data = json.loads(raw_text)
            if self.nlp:
                doc = self.nlp(user_input)
                parsed_data["entities"] = {
                    "people": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
                    "dates": [ent.text for ent in doc.ents if ent.label_ == "DATE"],
                    "orgs": [ent.text for ent in doc.ents if ent.label_ == "ORG"]
                }
            return parsed_data
            
        except Exception as e:
            print(f"Error parsing input: {e}")
            # Fallback: Use Local Regex Parser if API fails
            print("DEBUG: Rate limit hit, using fallback mock data.")
            from parser import parse_command
            local_data = parse_command(user_input)
            
            # Enrich local data with spaCy too!
            if self.nlp:
                doc = self.nlp(user_input)
                local_data["entities"] = {
                    "people": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
                    "dates": [ent.text for ent in doc.ents if ent.label_ == "DATE"],
                    "orgs": [ent.text for ent in doc.ents if ent.label_ == "ORG"]
                }
            return local_data

    def generate_smart_response(self, data: dict) -> str:
        """
        Generates a natural language response based on the project data.
        """
        prompt = f"""
        You are a senior project manager AI.
        Analyze the following project data and provide a professional status update.
        
        Data: {json.dumps(data, indent=2)}

        CRITICAL INSTRUCTIONS:
        1. If 'delayed_tasks' > 0, flag this as a RISK.
        2. If 'completion' < 50% and status is "In Progress", warn about slow progress.
        3. Provide 1 actionable recommendation based on the data.
        4. Keep it concise (max 3 sentences).
        5. Tone: Helpful, Professional, Insightful.
        """
        
        try:
            # Use a slightly more creative temperature if possible, but default is fine.
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"DEBUG: Smart response generation failed: {e}")
            # Fallback for API failure
            # Fallback for API failure - meaningful local analysis
            if data.get("intent") == "CREATE_PROJECT":
                return f"Project {data.get('project_name')} created successfully. (processed locally)"
            else:
                p_name = data.get('project_name')
                risk = data.get('risk_analysis', {})
                
                status_msg = f"Here is the status for {p_name}."
                
                if risk:
                    if risk.get("risk_level") == "HIGH":
                         status_msg += " 🔴 CRITICAL RISK DETECTED."
                    elif risk.get("risk_level") == "MEDIUM":
                         status_msg += " ⚠️ Warning: Project is at risk."
                    
                    if risk.get("risk_factors"):
                        factors = ", ".join(risk["risk_factors"])
                        status_msg += f" Issues: {factors}."
                
                return status_msg + " (Local Analysis)"
