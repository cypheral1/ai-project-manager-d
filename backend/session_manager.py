import redis
import json
from typing import List, Dict, Optional
from datetime import timedelta
from config import config

class SessionManager:
    """
    Manages conversation sessions using Redis for persistence.
    Falls back to in-memory storage if Redis is unavailable.
    Stores conversation history to enable context-aware responses.
    """
    
    def __init__(self, host=None, port=None, db=None):
        """Initialize Redis connection using config defaults."""
        self.use_redis = True
        self.fallback_storage = {}  # In-memory fallback
        self.fallback_projects = {}  # In-memory project refs
        
        try:
            self.redis_client = redis.Redis(
                host=host or config.REDIS_HOST,
                port=port or config.REDIS_PORT,
                db=db or config.REDIS_DB,
                decode_responses=True
            )
            # Test the connection
            self.redis_client.ping()
            print("DEBUG: SessionManager using Redis storage")
        except Exception as e:
            print(f"WARNING: Redis unavailable, using in-memory storage: {e}")
            self.use_redis = False
            self.redis_client = None
        
        self.session_ttl = timedelta(hours=config.REDIS_SESSION_TTL_HOURS)
        
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
        
        if self.use_redis:
            try:
                key = self._get_session_key(session_id)
                self.redis_client.rpush(key, json.dumps(message))
                self.redis_client.expire(key, self.session_ttl)
            except Exception as e:
                print(f"WARNING: Redis error, falling back: {e}")
                self.use_redis = False
                # Fall through to in-memory storage
        
        if not self.use_redis:
            if session_id not in self.fallback_storage:
                self.fallback_storage[session_id] = []
            self.fallback_storage[session_id].append(message)
    
    def get_conversation_history(self, session_id: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve the last N messages from a session.
        
        Args:
            session_id: Unique identifier for the conversation session
            limit: Number of recent messages to retrieve (default: 5)
            
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        if self.use_redis:
            try:
                key = self._get_session_key(session_id)
                messages = self.redis_client.lrange(key, -limit, -1)
                return [json.loads(msg) for msg in messages]
            except Exception as e:
                print(f"WARNING: Redis error: {e}")
                self.use_redis = False
        
        # Fallback
        messages = self.fallback_storage.get(session_id, [])
        return messages[-limit:] if messages else []
    
    def set_last_project_reference(self, session_id: str, project_name: str):
        """
        Store the most recently mentioned project name.
        
        Args:
            session_id: Unique identifier for the conversation session
            project_name: Name of the project
        """
        if self.use_redis:
            try:
                key = self._get_project_ref_key(session_id)
                self.redis_client.set(key, project_name, ex=self.session_ttl)
                return
            except Exception as e:
                print(f"WARNING: Redis error: {e}")
                self.use_redis = False
        
        # Fallback
        self.fallback_projects[session_id] = project_name
    
    def get_last_project_reference(self, session_id: str) -> Optional[str]:
        """
        Retrieve the most recently mentioned project name.
        
        Args:
            session_id: Unique identifier for the conversation session
            
        Returns:
            Project name if found, None otherwise
        """
        if self.use_redis:
            try:
                key = self._get_project_ref_key(session_id)
                return self.redis_client.get(key)
            except Exception as e:
                print(f"WARNING: Redis error: {e}")
                self.use_redis = False
        
        # Fallback
        return self.fallback_projects.get(session_id)
    
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
