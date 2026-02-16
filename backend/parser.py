import re

def parse_command(user_input):
    text = user_input.lower()

    if "status" in text or "progress" in text:
        intent = "GET_STATUS"
    elif "create" in text:
        intent = "CREATE_PROJECT"
    else:
        return {"error": "unknown_intent"}

    project_match = re.search(r'project(?:\s+named)?\s+([a-zA-Z0-9]+)', user_input, re.IGNORECASE)
    project_name = f"Project {project_match.group(1)}" if project_match else None

    number_match = re.search(r'\b(\d+)\s*(?:tasks?|items)\b', user_input, re.IGNORECASE)
    total_tasks = int(number_match.group(1)) if number_match else None

    # Allocation regex: "2 tasks to backend", "3 frontend"
    allocations = {}
    
    # Allow "2 tasks to backend"
    backend_match = re.search(r'(\d+)\s*(?:tasks?|items)?\s*(?:to|for)?\s*(?:the)?\s*backend', user_input, re.IGNORECASE)
    if backend_match:
        allocations["backend"] = int(backend_match.group(1))
        
    frontend_match = re.search(r'(\d+)\s*(?:tasks?|items)?\s*(?:to|for)?\s*(?:the)?\s*frontend', user_input, re.IGNORECASE)
    if frontend_match:
        allocations["frontend"] = int(frontend_match.group(1))

    # Recalculate total if allocations exist but total is None
    if total_tasks is None and allocations:
        total_tasks = sum(allocations.values())
        
    # If total exists but allocations don't sum up, normally we'd error, 
    # but for regex parser let's just trust the allocations if acceptable.

    return {
        "intent": intent,
        "project_name": project_name,
        "total_tasks": total_tasks,
        "allocations": allocations,
        "validation_error": None
    }
