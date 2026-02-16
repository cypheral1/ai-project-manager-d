import redis
import json
from typing import List, Dict, Optional
from datetime import timedelta

class SessionManager:
    """
    Manages conversation sessions using Redis for persistence.
    Stores conversation history to enable context-aware responses.
    """
    
    def __init__(self, host='localhost', port=6379, db=0):
        """Initialize Redis connection."""
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        self.session_ttl = timedelta(hours=1)  # Sessions expire after 1 hour of inactivity
        
    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for a session."""
        return f"session:{session_id}:messages"
    
    def _get_project_ref_key(self, session_id: str) -> str:
        """Generate Redis key for last project reference."""
        return f"session:{session_id}:last_project"
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Store a message in the conversation history.
        
        Args:
            session_id: Unique identifier for the conversation session
            role: Either 'user' or 'assistant'
            content: The message content
        """
        message = {
            "role": role,
            "content": content
        }
        
        key = self._get_session_key(session_id)
        self.redis_client.rpush(key, json.dumps(message))
        self.redis_client.expire(key, self.session_ttl)
    
    def get_conversation_history(self, session_id: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve the last N messages from a session.
        
        Args:
            session_id: Unique identifier for the conversation session
            limit: Number of recent messages to retrieve (default: 5)
            
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        key = self._get_session_key(session_id)
        messages = self.redis_client.lrange(key, -limit, -1)
        return [json.loads(msg) for msg in messages]
    
    def set_last_project_reference(self, session_id: str, project_name: str):
        """
        Store the most recently mentioned project name.
        
        Args:
            session_id: Unique identifier for the conversation session
            project_name: Name of the project
        """
        key = self._get_project_ref_key(session_id)
        self.redis_client.set(key, project_name, ex=self.session_ttl)
    
    def get_last_project_reference(self, session_id: str) -> Optional[str]:
        """
        Retrieve the most recently mentioned project name.
        
        Args:
            session_id: Unique identifier for the conversation session
            
        Returns:
            Project name if found, None otherwise
        """
        key = self._get_project_ref_key(session_id)
        return self.redis_client.get(key)
    
    def clear_session(self, session_id: str):
        """
        Delete all data for a session.
        
        Args:
            session_id: Unique identifier for the conversation session
        """
        msg_key = self._get_session_key(session_id)
        proj_key = self._get_project_ref_key(session_id)
        self.redis_client.delete(msg_key, proj_key)
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            return self.redis_client.ping()
        except:
            return False
