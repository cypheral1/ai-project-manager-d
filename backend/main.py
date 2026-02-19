from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from nlp_processor import NLPProcessor
from java_gateway import JavaGateway
from session_manager import SessionManager
from task_assigner import auto_assign_tasks, suggest_allocation, generate_java_payload
from validators import (
    validate_project_creation,
    validate_project_update,
    check_duplicate_project,
)
from config import config

app = FastAPI(
    title="AI Project Manager",
    description="Intelligent chatbot for project management powered by Gemini AI",
    version="2.0.0",
)

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

HELP_TEXT = """🤖 **AI Project Manager** — Here's what I can do:

• **Create a project**: "Create Project Alpha with 16 tasks, assign 7 to frontend (John, Sarah), 5 to backend (Mike, Tom), 4 to testing (Lisa)"
• **Check status**: "What's the status of Project Alpha?"
• **List projects**: "Show all projects"
• **Update a project**: "Update Project Alpha to 50% completion"
• **Delete a project**: "Delete Project Alpha"
• **Get help**: "Help" or "What can you do?"

I also remember context — try "What's the status of it?" after mentioning a project!"""


# ─── Request Models ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ProjectCreateRequest(BaseModel):
    name: str
    total_tasks: int = 0
    allocations: Optional[Dict] = None

class ProjectUpdateRequest(BaseModel):
    status: Optional[str] = None
    completion: Optional[int] = None
    delayed_tasks: Optional[int] = None

class AutoAssignRequest(BaseModel):
    total_tasks: int
    allocations: Dict
    task_descriptions: Optional[List[str]] = None


# ─── Chat Endpoint (Primary) ─────────────────────────────────────────────────

@app.post("/chat")
def chat(req: ChatRequest):
    # 0. Handle session
    session_id = req.session_id or "default"
    session_manager.add_message(session_id, "user", req.message)

    # 1. Parse Intent and Entities with AI
    parsed_data = nlp.parse_input(req.message)

    # 1.5. Handle pronoun references ("it", "that", etc.)
    if any(word in req.message.lower() for word in ["it", "that project", "the project"]) and not parsed_data.get("project_name"):
        last_project = session_manager.get_last_project_reference(session_id)
        if last_project:
            parsed_data["project_name"] = last_project

    intent = parsed_data.get("intent", "UNKNOWN")

    # ── HELP ──
    if intent == "HELP":
        session_manager.add_message(session_id, "assistant", HELP_TEXT)
        return {"intent": "HELP", "data": parsed_data, "response": HELP_TEXT}

    # ── UNKNOWN ──
    if intent == "UNKNOWN":
        msg = "I'm not sure what you mean. Try asking for project status, creating a project, or type 'help' for a list of commands."
        return {"response": msg}

    # ── LIST_PROJECTS ──
    if intent == "LIST_PROJECTS":
        projects = gateway.list_all_projects()
        if not projects:
            msg = "No projects found yet. Try creating one!"
        else:
            lines = [f"📋 **{len(projects)} project(s) found:**\n"]
            for p in projects:
                status_emoji = {"Created": "🆕", "In Progress": "🔄", "Completed": "✅", "On Hold": "⏸️", "Cancelled": "❌"}.get(p["status"], "📁")
                lines.append(f"  {status_emoji} **{p['name']}** — {p['status']} ({p['completion']}% complete, {p['total_tasks']} tasks)")
            msg = "\n".join(lines)
        session_manager.add_message(session_id, "assistant", msg)
        return {"intent": "LIST_PROJECTS", "data": {"projects": projects}, "response": msg}

    # ── GET_STATUS ──
    if intent == "GET_STATUS":
        project_name = parsed_data.get("project_name")
        if not project_name:
            return {"intent": "GET_STATUS", "data": parsed_data, "response": "Which project are you referring to?"}

        project_info = gateway.get_project_status(project_name)
        if not project_info:
            return {"intent": "GET_STATUS", "data": parsed_data, "response": f"I couldn't find any data for {project_name}."}

        parsed_data["project_data"] = project_info
        parsed_data["risk_analysis"] = gateway.analyze_project_risk(project_name)

    # ── CREATE_PROJECT ──
    elif intent == "CREATE_PROJECT":
        if parsed_data.get("validation_error"):
            return {"response": f"I can't create that project: {parsed_data['validation_error']}"}

        project_name = parsed_data.get("project_name")
        total_tasks = parsed_data.get("total_tasks", 0)
        allocations = parsed_data.get("allocations", {})

        # Check for duplicates
        if project_name and check_duplicate_project(gateway.db, project_name):
            return {"response": f"A project named '{project_name}' already exists. Choose a different name."}

        # Validate
        valid, error = validate_project_creation(project_name or "", total_tasks or 0, allocations or None)
        if not valid:
            return {"response": f"Validation error: {error}"}

        # Auto-assign tasks within teams
        if allocations:
            allocations = auto_assign_tasks(total_tasks or 0, allocations)

        result = gateway.create_project(project_name, total_tasks, allocations)
        parsed_data["backend_result"] = result

        # Generate structured Java payload
        if allocations:
            parsed_data["java_payload"] = generate_java_payload(
                project_name, total_tasks or 0, allocations
            )

    # ── UPDATE_TASK ──
    elif intent == "UPDATE_TASK":
        project_name = parsed_data.get("project_name")
        if not project_name:
            return {"response": "Which project should I update?"}

        update_fields = parsed_data.get("update_fields", {})
        if not update_fields:
            return {"response": "What should I update? (e.g., status, completion %)"}

        valid, error = validate_project_update(**update_fields)
        if not valid:
            return {"response": f"Validation error: {error}"}

        result = gateway.update_project_status(project_name, **update_fields)
        parsed_data["backend_result"] = result
        if not result.get("success"):
            return {"response": result.get("message", f"Could not update {project_name}.")}

    # ── DELETE_PROJECT ──
    elif intent == "DELETE_PROJECT":
        project_name = parsed_data.get("project_name")
        if not project_name:
            return {"response": "Which project should I delete?"}

        result = gateway.delete_project(project_name)
        parsed_data["backend_result"] = result
        if not result.get("success"):
            return {"response": result.get("message", f"Could not delete {project_name}.")}

    # 3. Generate natural language response
    final_response = nlp.generate_smart_response(parsed_data)

    # 4. Store assistant response and project reference
    session_manager.add_message(session_id, "assistant", final_response)
    if parsed_data.get("project_name"):
        session_manager.set_last_project_reference(session_id, parsed_data["project_name"])

    return {
        "intent": intent,
        "data": parsed_data,
        "response": final_response
    }


# ─── REST Endpoints (Direct CRUD for Java Backend) ───────────────────────────

@app.get("/projects")
def list_projects():
    """List all projects with summary data."""
    projects = gateway.list_all_projects()
    return {"projects": projects, "total": len(projects)}


@app.get("/projects/{name}")
def get_project(name: str):
    """Get a single project with risk analysis."""
    project = gateway.get_project_status(name)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found.")
    risk = gateway.analyze_project_risk(name)
    return {"project": project, "risk_analysis": risk}


@app.post("/projects", status_code=201)
def create_project(req: ProjectCreateRequest):
    """Create a new project via direct JSON."""
    if check_duplicate_project(gateway.db, req.name):
        raise HTTPException(status_code=409, detail=f"Project '{req.name}' already exists.")

    valid, error = validate_project_creation(req.name, req.total_tasks, req.allocations)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    allocations = req.allocations or {}
    if allocations:
        allocations = auto_assign_tasks(req.total_tasks, allocations)

    result = gateway.create_project(req.name, req.total_tasks, allocations)
    java_payload = generate_java_payload(req.name, req.total_tasks, allocations)

    return {"result": result, "java_payload": java_payload}


@app.put("/projects/{name}")
def update_project(name: str, req: ProjectUpdateRequest):
    """Update a project's status, completion, or delayed tasks."""
    update_fields = {k: v for k, v in req.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update.")

    valid, error = validate_project_update(**update_fields)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    result = gateway.update_project_status(name, **update_fields)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))

    return result


@app.delete("/projects/{name}")
def delete_project(name: str):
    """Delete a project by name."""
    result = gateway.delete_project(name)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


@app.post("/tasks/auto-assign")
def auto_assign(req: AutoAssignRequest):
    """Run intelligent task auto-assignment."""
    enhanced = auto_assign_tasks(
        req.total_tasks, req.allocations, req.task_descriptions
    )
    return {
        "allocations": enhanced,
        "total_tasks": req.total_tasks,
        "java_payload": generate_java_payload(
            "auto-assign", req.total_tasks, enhanced
        )
    }


@app.get("/health")
def health():
    return gateway.health_check()
#abc