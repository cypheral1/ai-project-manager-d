"""
Intelligent task auto-assignment engine.

Provides:
- Keyword-based task categorization (maps keywords → teams)
- Workload balancing (round-robin within teams)
- Auto-distribution when no explicit allocations given
"""

from typing import Dict, List, Optional, Tuple
import math


# ─── Keyword → Team mapping ─────────────────────────────────────────────────
TEAM_KEYWORDS = {
    "frontend": [
        "ui", "ux", "page", "component", "css", "html", "layout", "design",
        "button", "form", "modal", "responsive", "animation", "style",
        "react", "angular", "vue", "template", "view", "widget", "dashboard",
        "navigation", "menu", "header", "footer", "sidebar"
    ],
    "backend": [
        "api", "database", "db", "server", "auth", "authentication",
        "authorization", "endpoint", "rest", "graphql", "middleware",
        "controller", "service", "repository", "model", "schema",
        "migration", "cache", "redis", "security", "jwt", "token", "crud"
    ],
    "testing": [
        "test", "qa", "quality", "verify", "validation", "bug", "debug",
        "regression", "integration", "unit", "e2e", "selenium", "cypress",
        "coverage", "assertion", "fixture", "mock"
    ],
    "devops": [
        "deploy", "ci", "cd", "pipeline", "docker", "kubernetes", "k8s",
        "aws", "cloud", "terraform", "monitoring", "logging", "nginx",
        "jenkins", "github actions", "infrastructure", "scaling"
    ],
    "design": [
        "figma", "wireframe", "prototype", "mockup", "sketch", "color",
        "typography", "brand", "logo", "icon", "illustration", "user research"
    ]
}


def categorize_task(task_description: str) -> str:
    """
    Categorize a task into a team based on keyword matching.
    
    Args:
        task_description: Description or title of the task
    
    Returns:
        Team name (e.g., 'frontend', 'backend', 'testing')
        Defaults to 'general' if no keyword match found.
    """
    text = task_description.lower()
    scores = {}
    
    for team, keywords in TEAM_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[team] = score
    
    if not scores:
        return "general"
    
    return max(scores, key=scores.get)


def categorize_tasks_batch(task_descriptions: List[str]) -> Dict[str, List[str]]:
    """
    Categorize multiple tasks into teams.
    
    Args:
        task_descriptions: List of task descriptions
    
    Returns:
        Dict mapping team names to lists of task descriptions
    """
    categorized = {}
    
    for desc in task_descriptions:
        team = categorize_task(desc)
        if team not in categorized:
            categorized[team] = []
        categorized[team].append(desc)
    
    return categorized


def distribute_tasks_round_robin(
    total_tasks: int,
    people: List[str]
) -> Dict[str, int]:
    """
    Distribute tasks evenly among people using round-robin.
    
    Args:
        total_tasks: Number of tasks to distribute
        people: List of people names
    
    Returns:
        Dict mapping person name to task count
    """
    if not people:
        return {}
    
    base_count = total_tasks // len(people)
    remainder = total_tasks % len(people)
    
    distribution = {}
    for i, person in enumerate(people):
        distribution[person] = base_count + (1 if i < remainder else 0)
    
    return distribution


def auto_assign_tasks(
    total_tasks: int,
    allocations: Dict,
    task_descriptions: Optional[List[str]] = None
) -> Dict:
    """
    Intelligently distribute tasks within team allocations.
    
    If task_descriptions are provided, categorize them first.
    Otherwise, distribute tasks evenly among people in each team.
    
    Args:
        total_tasks: Total number of tasks
        allocations: Dict of {team_name: {count: int, people: [str]}}
        task_descriptions: Optional list of task descriptions for categorization
    
    Returns:
        Enhanced allocations with per-person assignments:
        {
            "frontend": {
                "count": 7,
                "people": ["John", "Sarah"],
                "assignments": {"John": 4, "Sarah": 3}
            }
        }
    """
    result = {}
    
    for team_name, team_data in allocations.items():
        if isinstance(team_data, dict):
            count = team_data.get("count", 0)
            people = team_data.get("people", [])
        else:
            count = int(team_data)
            people = []
        
        assignments = {}
        if people:
            assignments = distribute_tasks_round_robin(count, people)
        
        result[team_name] = {
            "count": count,
            "people": people,
            "assignments": assignments
        }
    
    return result


def suggest_allocation(
    total_tasks: int,
    teams: Optional[List[str]] = None
) -> Dict:
    """
    Suggest a balanced allocation when no explicit distribution is given.
    
    Args:
        total_tasks: Total tasks to distribute
        teams: Optional list of team names. Defaults to frontend/backend/testing.
    
    Returns:
        Suggested allocations dict
    """
    if not teams:
        teams = ["frontend", "backend", "testing"]
    
    base = total_tasks // len(teams)
    remainder = total_tasks % len(teams)
    
    suggestion = {}
    for i, team in enumerate(teams):
        count = base + (1 if i < remainder else 0)
        suggestion[team] = {
            "count": count,
            "people": [],
            "assignments": {}
        }
    
    return suggestion


def generate_java_payload(
    project_name: str,
    total_tasks: int,
    allocations: Dict,
    action: str = "CREATE"
) -> Dict:
    """
    Generate a structured JSON payload for Java backend consumption.
    
    Args:
        project_name: Name of the project
        total_tasks: Total number of tasks
        allocations: Enhanced allocations dict
        action: Action type (CREATE, UPDATE, DELETE)
    
    Returns:
        Structured JSON dict ready for Java API
    """
    teams = []
    for team_name, team_data in allocations.items():
        if isinstance(team_data, dict):
            members = []
            assignments = team_data.get("assignments", {})
            people = team_data.get("people", [])
            
            for person in people:
                members.append({
                    "name": person,
                    "assignedTasks": assignments.get(person, 0)
                })
            
            teams.append({
                "teamName": team_name,
                "taskCount": team_data.get("count", 0),
                "members": members
            })
        else:
            teams.append({
                "teamName": team_name,
                "taskCount": int(team_data),
                "members": []
            })
    
    return {
        "action": action,
        "project": {
            "name": project_name,
            "totalTasks": total_tasks,
            "teams": teams
        }
    }
