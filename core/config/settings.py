
"""
Application Settings with Pydantic
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration"""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    workers: int = 1  # Use 1 worker for development (avoids Prometheus metrics conflicts)
    
    # Supabase Configuration (REQUIRED)
    # Supports both VITE_ prefixed (from frontend) and direct names
    supabase_url: str = ""
    supabase_key: str = ""  # Service role key for backend operations
    supabase_anon_key: str = ""  # Anon key for client verification
    
    # Support for VITE_ prefixed variables (from frontend .env)
    vite_supabase_url: str = ""
    vite_supabase_anon_key: str = ""
    vite_supabase_service_key: str = ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use VITE_ prefixed if direct names not provided
        if not self.supabase_url and self.vite_supabase_url:
            self.supabase_url = self.vite_supabase_url
        if not self.supabase_anon_key and self.vite_supabase_anon_key:
            self.supabase_anon_key = self.vite_supabase_anon_key
        if not self.supabase_key and self.vite_supabase_service_key:
            self.supabase_key = self.vite_supabase_service_key
        
        # Validate required fields
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL or VITE_SUPABASE_URL is required")
        if not self.supabase_key:
            raise ValueError("SUPABASE_KEY or VITE_SUPABASE_SERVICE_KEY is required")
        if not self.supabase_anon_key:
            raise ValueError("SUPABASE_ANON_KEY or VITE_SUPABASE_ANON_KEY is required")
    
    # Storage
    storage_bucket: str = "gamoraai-projects"
    
    # AI API Keys (REQUIRED)
    openai_api_key: str
    deepseek_api_key: str
    
    # Godot
    godot_path: str = "/usr/local/bin/godot"
    projects_dir: str = "./projects"
    
    # Monitoring (Optional)
    sentry_dsn: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields like VITE_* variables
