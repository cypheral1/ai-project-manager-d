import requests
from db_manager import DatabaseManager

class JavaGateway:
    """
    Acts as a bridge to the Java backend. 
    Now using SQLite database for persistence.
    """
    def __init__(self, backend_url=None):
        self.backend_url = backend_url
        self.db = DatabaseManager(db_path="projects.db")

    def get_project_status(self, project_name):
        """Get project status from database."""
        return self.db.get_project(project_name)

    def analyze_project_risk(self, project_name):
        """
        Calculates a deterministic risk score for a project.
        Returns: {
            "risk_score": int (0-100),
            "risk_level": "LOW" | "MEDIUM" | "HIGH",
            "risk_factors": list[str]
        }
        """
        project = self.db.get_project(project_name)
        if not project:
            return None

        score = 0
        factors = []

        # Factor 1: Delayed Tasks (High Impact)
        delayed = project.get("delayed_tasks", 0)
        if delayed > 0:
            score += delayed * 10
            factors.append(f"{delayed} delayed tasks")

        # Factor 2: Low Completion (Medium Impact)
        completion = project.get("completion", 0)
        status = project.get("status", "")
        if status == "In Progress" and completion < 20:
             score += 20
             factors.append("Low completion rate (<20%)")

        # Cap score at 100
        score = min(score, 100)

        # Determine Level
        if score >= 50:
            level = "HIGH"
        elif score >= 20:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "risk_score": score,
            "risk_level": level,
            "risk_factors": factors
        }

    def create_project(self, project_name, total_tasks, allocations):
        """Create a new project in database."""
        result = self.db.create_project(project_name, total_tasks, allocations)
        return {"success": True, "message": f"Project {project_name} created with detailed assignments."}

    def health_check(self):
        return {"status": "Java Gateway is active (SQLite Database: ON)"}
