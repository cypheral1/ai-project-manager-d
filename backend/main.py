from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from nlp_processor import NLPProcessor
from java_gateway import JavaGateway
from session_manager import SessionManager
from config import config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
nlp = NLPProcessor()
gateway = JavaGateway()
session_manager = SessionManager()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Frontend sends this

@app.post("/chat")
def chat(req: ChatRequest):
    # 0. Handle session (use 'default' if not provided)
    session_id = req.session_id or "default"
    
    # Store user message in session
    session_manager.add_message(session_id, "user", req.message)
    
    # 1. Parse Intent and Entities with AI
    parsed_data = nlp.parse_input(req.message)
    
    # 1.5. Handle pronoun references ("it", "that", etc.)
    if any(word in req.message.lower() for word in ["it", "that project", "the project"]) and not parsed_data.get("project_name"):
        last_project = session_manager.get_last_project_reference(session_id)
        if last_project:
            parsed_data["project_name"] = last_project

    if parsed_data.get("intent") == "UNKNOWN":
        return {
            "response": "I'm not sure what you mean. Try asking for project status or creating a project."
        }
    
    # 2. Handle specific intents
    response_data = {}
    
    if parsed_data["intent"] == "GET_STATUS":
        project_name = parsed_data.get("project_name")
        if not project_name:
            return {
                "intent": "GET_STATUS",
                "data": parsed_data,
                "response": "Which project are you referring to?"
            }
            
        project_info = gateway.get_project_status(project_name)
        if not project_info:
            return {
                "intent": "GET_STATUS",
                "data": parsed_data,
                "response": f"I couldn't find any data for {project_name}."
            }
            
        # Add retrieved data and RISK ANALYSIS to the context
        parsed_data["project_data"] = project_info
        parsed_data["risk_analysis"] = gateway.analyze_project_risk(project_name)
        
    elif parsed_data["intent"] == "CREATE_PROJECT":
        # Check for validation errors from the NLP stage
        if parsed_data.get("validation_error"):
            return {
                "response": f"I can't create that project: {parsed_data['validation_error']}"
            }
            
        # Execute creation in backend
        result = gateway.create_project(
            parsed_data.get("project_name"),
            parsed_data.get("total_tasks"),
            parsed_data.get("allocations")
        )
        parsed_data["backend_result"] = result

    # 3. Generate natural language response
    final_response = nlp.generate_smart_response(parsed_data)
    
    # 4. Store assistant response and project reference
    session_manager.add_message(session_id, "assistant", final_response)
    if parsed_data.get("project_name"):
        session_manager.set_last_project_reference(session_id, parsed_data["project_name"])
    
    return {
        "intent": parsed_data["intent"],
        "data": parsed_data,
        "response": final_response
    }

@app.get("/health")
def health():
    return gateway.health_check()

