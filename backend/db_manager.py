from database import Database
from typing import Optional, Dict, List, Any

class DatabaseManager:
    """
    Manages CRUD operations for projects using SQLite.
    """
    
    def __init__(self, db_path='projects.db'):
        self.db = Database(db_path)
    
    def create_project(self, name: str, total_tasks: int = 0, allocations: Dict = None) -> Dict:
        """
        Create a new project with allocations.
        
        Args:
            name: Project name
            total_tasks: Total number of tasks
            allocations: Dict of {team_name: {count: int, people: [str]}}
        
        Returns:
            Created project data
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert project
            cursor.execute('''
                INSERT INTO projects (name, total_tasks, status, completion, delayed_tasks)
                VALUES (?, ?, 'Created', 0, 0)
            ''', (name, total_tasks))
            
            project_id = cursor.lastrowid
            
            # Insert allocations if provided
            if allocations:
                for team_name, team_data in allocations.items():
                    if isinstance(team_data, dict):
                        count = team_data.get('count', 0)
                        people = team_data.get('people', [])
                    else:
                        # Handle old format (just numbers)
                        count = team_data
                        people = []
                    
                    cursor.execute('''
                        INSERT INTO allocations (project_id, team_name, task_count)
                        VALUES (?, ?, ?)
                    ''', (project_id, team_name, count))
                    
                    allocation_id = cursor.lastrowid
                    
                    # Insert team members
                    for person in people:
                        cursor.execute('''
                            INSERT INTO team_members (allocation_id, person_name)
                            VALUES (?, ?)
                        ''', (allocation_id, person))
            
            conn.commit()
            return self.get_project(name)
    
    def get_project(self, name: str) -> Optional[Dict]:
        """
        Retrieve a project by name.
        
        Args:
            name: Project name
        
        Returns:
            Project data dict or None if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get project
            cursor.execute('''
                SELECT * FROM projects WHERE name = ?
            ''', (name,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            project = {
                'status': row['status'],
                'completion': row['completion'],
                'delayed_tasks': row['delayed_tasks'],
                'total_tasks': row['total_tasks']
            }
            
            # Get allocations
            cursor.execute('''
                SELECT id, team_name, task_count 
                FROM allocations 
                WHERE project_id = ?
            ''', (row['id'],))
            
            allocations = {}
            for alloc_row in cursor.fetchall():
                # Get team members
                cursor.execute('''
                    SELECT person_name 
                    FROM team_members 
                    WHERE allocation_id = ?
                ''', (alloc_row['id'],))
                
                people = [member['person_name'] for member in cursor.fetchall()]
                
                allocations[alloc_row['team_name']] = {
                    'count': alloc_row['task_count'],
                    'people': people
                }
            
            project['allocations'] = allocations
            return project
    
    def update_project(self, name: str, **kwargs) -> bool:
        """
        Update project fields.
        
        Args:
            name: Project name
            **kwargs: Fields to update (status, completion, delayed_tasks, total_tasks)
        
        Returns:
            True if updated, False if not found
        """
        allowed_fields = ['status', 'completion', 'delayed_tasks', 'total_tasks']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build update query
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [name]
            
            cursor.execute(f'''
                UPDATE projects 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
            ''', values)
            
            return cursor.rowcount > 0
    
    def delete_project(self, name: str) -> bool:
        """
        Delete a project (cascades to allocations and team members).
        
        Args:
            name: Project name
        
        Returns:
            True if deleted, False if not found
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM projects WHERE name = ?', (name,))
            return cursor.rowcount > 0
    
    def list_all_projects(self) -> List[str]:
        """
        Get list of all project names.
        
        Returns:
            List of project names
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM projects ORDER BY created_at DESC')
            return [row['name'] for row in cursor.fetchall()]
    
    def search_projects(self, query: str) -> List[Dict]:
        """
        Search projects by partial name match.
        
        Args:
            query: Search string (partial match)
        
        Returns:
            List of matching project summaries
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT name, status, completion, total_tasks, delayed_tasks '
                'FROM projects WHERE name LIKE ? ORDER BY created_at DESC',
                (f'%{query}%',)
            )
            return [
                {
                    'name': row['name'],
                    'status': row['status'],
                    'completion': row['completion'],
                    'total_tasks': row['total_tasks'],
                    'delayed_tasks': row['delayed_tasks']
                }
                for row in cursor.fetchall()
            ]
    
    def get_all_projects_summary(self) -> List[Dict]:
        """
        Get a summary of all projects (for LIST_PROJECTS intent).
        
        Returns:
            List of project summary dicts
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT name, status, completion, total_tasks, delayed_tasks, '
                'created_at FROM projects ORDER BY created_at DESC'
            )
            return [
                {
                    'name': row['name'],
                    'status': row['status'],
                    'completion': row['completion'],
                    'total_tasks': row['total_tasks'],
                    'delayed_tasks': row['delayed_tasks'],
                    'created_at': row['created_at']
                }
                for row in cursor.fetchall()
            ]
