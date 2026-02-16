from backend.db_manager import DatabaseManager
import json

db = DatabaseManager('projects.db')

print("=" * 80)
print("ALL PROJECTS IN DATABASE")
print("=" * 80)

projects = db.list_all_projects()
print(f"\nFound {len(projects)} projects:\n")

for project_name in projects:
    project = db.get_project(project_name)
    print(f"📊 {project_name}")
    print(f"   Status: {project['status']}")
    print(f"   Total Tasks: {project['total_tasks']}")
    print(f"   Completion: {project['completion']}%")
    print(f"   Delayed: {project['delayed_tasks']}")
    
    if project['allocations']:
        print(f"   Teams:")
        for team, data in project['allocations'].items():
            people = ", ".join(data['people']) if data['people'] else "No one assigned"
            print(f"      - {team}: {data['count']} tasks ({people})")
    print()
