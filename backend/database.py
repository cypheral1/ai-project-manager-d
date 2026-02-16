import sqlite3
import os
from contextlib import contextmanager

class Database:
    """
    SQLite database connection and schema management.
    """
    
    def __init__(self, db_path='projects.db'):
        """Initialize database connection."""
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Create tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'Created',
                    completion INTEGER DEFAULT 0,
                    delayed_tasks INTEGER DEFAULT 0,
                    total_tasks INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Allocations table (team assignments)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS allocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    team_name TEXT NOT NULL,
                    task_count INTEGER DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            ''')
            
            # Team members table (people assigned to teams)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS team_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    allocation_id INTEGER NOT NULL,
                    person_name TEXT NOT NULL,
                    FOREIGN KEY (allocation_id) REFERENCES allocations(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_projects_name 
                ON projects(name)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_allocations_project 
                ON allocations(project_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_members_allocation 
                ON team_members(allocation_id)
            ''')
            
            conn.commit()
