"""
Local regex-based fallback parser.
Used when the Gemini API is unavailable or rate-limited.
Handles all 6 intents and extracts teams + people from parentheses.
"""

import re
from typing import Dict, List, Optional


# ─── Team patterns (regex fragments) ────────────────────────────────────────
TEAM_PATTERNS = [
    "frontend", "backend", "testing", "design", "devops", "qa",
    "mobile", "data", "infra", "security", "support"
]


def _extract_intent(text: str) -> str:
    """Determine user intent from input text."""
    lower = text.lower()

    # Check more specific intents FIRST to avoid keyword overlap
    # "update on" is a status query, not a task update — check first
    if any(w in lower for w in ["update on", "status", "progress", "how is", "doing", "tell me about"]):
        return "GET_STATUS"
    elif any(w in lower for w in ["update", "change status", "mark as", "mark ", "set completion", "set status"]):
        return "UPDATE_TASK"
    elif any(w in lower for w in ["create", "new project", "set up", "add project", "build"]):
        return "CREATE_PROJECT"
    elif any(w in lower for w in ["list", "show all", "all projects", "which projects"]):
        return "LIST_PROJECTS"
    elif any(w in lower for w in ["delete", "remove", "drop"]):
        return "DELETE_PROJECT"
    elif any(w in lower for w in ["help", "what can you do", "commands", "usage"]):
        return "HELP"
    else:
        return "UNKNOWN"


def _extract_project_name(text: str) -> Optional[str]:
    """Extract project name from user input."""
    # Match patterns like: "Project Alpha", "project named Beta"
    match = re.search(
        r'project(?:\s+named)?\s+([A-Za-z0-9][A-Za-z0-9_ -]*)',
        text, re.IGNORECASE
    )
    if match:
        name = match.group(1).strip()
        # Remove trailing common words that aren't part of the name
        name = re.sub(r'\s+(with|having|and|to|for)\s*$', '', name, flags=re.IGNORECASE)
        return f"Project {name}" if not name.lower().startswith("project") else name

    return None


def _extract_total_tasks(text: str) -> Optional[int]:
    """Extract total task count from user input."""
    match = re.search(r'\b(\d+)\s*(?:tasks?|items?)\b', text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _extract_people_from_parens(text_segment: str) -> List[str]:
    """
    Extract people names from parentheses.
    e.g., "(John, Sarah)" → ["John", "Sarah"]
    e.g., "(John and Sarah)" → ["John", "Sarah"]
    """
    match = re.search(r'\(([^)]+)\)', text_segment)
    if not match:
        return []

    inside = match.group(1)
    # Split by comma or 'and'
    names = re.split(r'\s*,\s*|\s+and\s+', inside)
    return [n.strip() for n in names if n.strip()]


def _extract_allocations(text: str) -> Dict:
    """
    Extract team allocations with people from user input.

    Handles patterns like:
    - "7 to frontend (John, Sarah)"
    - "assign 5 to backend team (Mike, Tom)"
    - "3 tasks for testing (Lisa)"
    """
    allocations = {}
    teams_pattern = "|".join(TEAM_PATTERNS)

    # Pattern: <number> [tasks] [to/for] <team> [(people)]
    pattern = re.compile(
        r'(\d+)\s*(?:tasks?|items?)?\s*(?:to|for)?\s*(?:the\s+)?'
        r'(' + teams_pattern + r')'
        r'(?:\s+team)?'
        r'(?:\s*\(([^)]*)\))?',
        re.IGNORECASE
    )

    for match in pattern.finditer(text):
        count = int(match.group(1))
        team = match.group(2).lower()
        people_str = match.group(3)

        people = []
        if people_str:
            people = re.split(r'\s*,\s*|\s+and\s+', people_str)
            people = [p.strip() for p in people if p.strip()]

        allocations[team] = {
            "count": count,
            "people": people
        }

    # Also try: "assign <number> to <person> for <team>"
    person_pattern = re.compile(
        r'assign\s+(\d+)\s+to\s+([A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+)*)\s+for\s+(' + teams_pattern + r')',
        re.IGNORECASE
    )
    for match in person_pattern.finditer(text):
        count = int(match.group(1))
        people_str = match.group(2)
        team = match.group(3).lower()

        people = re.split(r'\s+and\s+', people_str)
        people = [p.strip() for p in people if p.strip()]

        if team not in allocations:
            allocations[team] = {"count": count, "people": people}

    return allocations


def _extract_status_update(text: str) -> Dict:
    """Extract status update fields from input."""
    result = {}

    # Completion percentage
    comp_match = re.search(r'(\d+)\s*%?\s*(?:complete|completion|done)', text, re.IGNORECASE)
    if comp_match:
        result["completion"] = int(comp_match.group(1))

    # Status
    status_keywords = {
        "in progress": "In Progress",
        "completed": "Completed",
        "on hold": "On Hold",
        "cancelled": "Cancelled",
        "created": "Created"
    }
    lower = text.lower()
    for keyword, status in status_keywords.items():
        if keyword in lower:
            result["status"] = status
            break

    return result


def parse_command(user_input: str) -> dict:
    """
    Parse a user command using regex patterns.
    Returns a structured dict compatible with the NLP processor output.

    Args:
        user_input: Raw text from user

    Returns:
        dict with intent, project_name, total_tasks, allocations, etc.
    """
    intent = _extract_intent(user_input)
    project_name = _extract_project_name(user_input)
    total_tasks = _extract_total_tasks(user_input)
    allocations = _extract_allocations(user_input)

    # Recalculate total if allocations exist but total is None
    if total_tasks is None and allocations:
        total_tasks = sum(
            a["count"] if isinstance(a, dict) else a
            for a in allocations.values()
        )

    # Validate allocation sum
    validation_error = None
    if total_tasks and allocations:
        alloc_sum = sum(
            a["count"] if isinstance(a, dict) else a
            for a in allocations.values()
        )
        if alloc_sum != total_tasks:
            validation_error = (
                f"Allocation mismatch: {alloc_sum} allocated vs {total_tasks} total tasks."
            )

    result = {
        "intent": intent,
        "project_name": project_name,
        "total_tasks": total_tasks,
        "allocations": allocations,
        "validation_error": validation_error
    }

    # Add status update fields for UPDATE_TASK intent
    if intent == "UPDATE_TASK":
        result["update_fields"] = _extract_status_update(user_input)

    return result
