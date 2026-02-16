import json
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from db_manager import DatabaseManager

print("=" * 80)
print("MIGRATING DATA FROM JSON TO SQLITE")
print("=" * 80)

# Initialize database
db = DatabaseManager(db_path="projects.db")

# Read existing JSON files
json_files = ["projects.json", "backend/projects.json"]
all_projects = {}

for json_file in json_files:
    if os.path.exists(json_file):
        print(f"\n📂 Found: {json_file}")
        with open(json_file, 'r') as f:
            projects_data = json.load(f)
            all_projects.update(projects_data)
            print(f"   Loaded {len(projects_data)} projects")

if not all_projects:
    print("\n⚠️ No JSON files found. Nothing to migrate.")
    sys.exit(0)

# Migrate each project
print(f"\n🚀 Migrating {len(all_projects)} projects to SQLite...")
migrated = 0
skipped = 0

for project_name, project_data in all_projects.items():
    try:
        # Check if project already exists
        existing = db.get_project(project_name)
        if existing:
            print(f"   ⏭️  Skipped: {project_name} (already in database)")
            skipped += 1
            continue
        
        # Extract data
        total_tasks = project_data.get('total_tasks', 0)
        allocations = project_data.get('allocations', {})
        
        # Create project in database
        db.create_project(project_name, total_tasks, allocations)
        
        # Update status and completion if provided
        if 'status' in project_data or 'completion' in project_data or 'delayed_tasks' in project_data:
            db.update_project(
                project_name,
                status=project_data.get('status', 'Created'),
                completion=project_data.get('completion', 0),
                delayed_tasks=project_data.get('delayed_tasks', 0)
            )
        
        print(f"   ✅ Migrated: {project_name}")
        migrated += 1
        
    except Exception as e:
        print(f"   ❌ Error migrating {project_name}: {e}")

# Summary
print("\n" + "=" * 80)
print("MIGRATION COMPLETE")
print("=" * 80)
print(f"✅ Migrated: {migrated} projects")
print(f"⏭️  Skipped: {skipped} projects")
print(f"\n📊 Total projects in database: {len(db.list_all_projects())}")

# Backup JSON files
for json_file in json_files:
    if os.path.exists(json_file):
        backup_file = f"{json_file}.backup"
        os.rename(json_file, backup_file)
        print(f"📦 Backed up: {json_file} → {backup_file}")

print("\n🎉 Migration successful! Projects are now in SQLite database.")
print("   Database file: projects.db")
print("\nTo view data:")
print("   sqlite3 projects.db")
print("   sqlite> SELECT * FROM projects;")
