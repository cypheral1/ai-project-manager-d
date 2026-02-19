"""
Centralized input validation for project management operations.
Ensures data integrity before any database writes.
"""

from typing import Dict, List, Optional, Tuple


class ValidationError(Exception):
    """Custom exception for validation failures."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_project_creation(
    name: str,
    total_tasks: int,
    allocations: Optional[Dict] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate all inputs for project creation.
    
    Returns:
        (True, None) if valid, (False, error_message) if invalid.
    """
    # Name validation
    if not name or not name.strip():
        return False, "Project name cannot be empty."
    
    if len(name.strip()) > 100:
        return False, "Project name cannot exceed 100 characters."
    
    # Total tasks validation
    if total_tasks is None:
        return False, "Total tasks must be specified."
    
    if not isinstance(total_tasks, int) or total_tasks < 0:
        return False, "Total tasks must be a non-negative integer."
    
    if total_tasks > 1000:
        return False, "Total tasks cannot exceed 1000 per project."
    
    # Allocation validation
    if allocations:
        valid, error = validate_allocations(allocations, total_tasks)
        if not valid:
            return False, error
    
    return True, None


def validate_allocations(
    allocations: Dict,
    total_tasks: int
) -> Tuple[bool, Optional[str]]:
    """
    Validate team allocations.
    
    Checks:
    - Each allocation count is a positive integer
    - Sum of allocations matches total_tasks
    - People lists contain valid strings
    """
    if not isinstance(allocations, dict):
        return False, "Allocations must be a dictionary."
    
    total_allocated = 0
    
    for team_name, team_data in allocations.items():
        if not team_name or not team_name.strip():
            return False, "Team name cannot be empty."
        
        if isinstance(team_data, dict):
            count = team_data.get("count", 0)
            people = team_data.get("people", [])
        elif isinstance(team_data, (int, float)):
            count = int(team_data)
            people = []
        else:
            return False, f"Invalid allocation format for team '{team_name}'."
        
        if not isinstance(count, int) or count < 0:
            return False, f"Task count for '{team_name}' must be a non-negative integer."
        
        if count == 0:
            return False, f"Task count for '{team_name}' cannot be zero."
        
        # Validate people list
        if not isinstance(people, list):
            return False, f"People list for '{team_name}' must be an array."
        
        for person in people:
            if not isinstance(person, str) or not person.strip():
                return False, f"Invalid person name in '{team_name}' team."
        
        total_allocated += count
    
    # Sum check
    if total_tasks and total_allocated != total_tasks:
        parts = []
        for k, v in allocations.items():
            cnt = v.get("count", v) if isinstance(v, dict) else v
            parts.append(f"{cnt} {k}")
        detail = " + ".join(parts)
        return False, (
            f"Allocation mismatch: assigned {total_allocated} tasks "
            f"but total is {total_tasks}. "
            f"({detail} = {total_allocated})"
        )
    
    return True, None


def check_duplicate_project(db_manager, project_name: str) -> bool:
    """
    Check if a project with the given name already exists.
    
    Returns:
        True if duplicate exists, False otherwise.
    """
    existing = db_manager.get_project(project_name)
    return existing is not None


def validate_project_update(
    status: Optional[str] = None,
    completion: Optional[int] = None,
    delayed_tasks: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate project update fields.
    """
    valid_statuses = {"Created", "In Progress", "Completed", "On Hold", "Cancelled"}
    
    if status is not None and status not in valid_statuses:
        return False, f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
    
    if completion is not None:
        if not isinstance(completion, int) or completion < 0 or completion > 100:
            return False, "Completion must be an integer between 0 and 100."
    
    if delayed_tasks is not None:
        if not isinstance(delayed_tasks, int) or delayed_tasks < 0:
            return False, "Delayed tasks must be a non-negative integer."
    
    return True, None
