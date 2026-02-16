import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Centralized configuration management.
    All values can be overridden via environment variables.
    """
    
    # Google Gemini AI
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'projects.db')
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_SESSION_TTL_HOURS = int(os.getenv('REDIS_SESSION_TTL_HOURS', '1'))
    
    # Backend API
    BACKEND_HOST = os.getenv('BACKEND_HOST', '0.0.0.0')
    BACKEND_PORT = int(os.getenv('BACKEND_PORT', '8000'))
    
    # CORS (Frontend URLs that can access the backend)
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:4200')
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', FRONTEND_URL).split(',')
    
    # Java Backend (future integration)
    JAVA_BACKEND_URL = os.getenv('JAVA_BACKEND_URL', None)
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is not set. Get one at https://ai.google.dev/")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(errors))
        
        return True

# Singleton instance
config = Config()
