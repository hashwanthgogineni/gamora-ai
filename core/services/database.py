"""
Supabase Database Service
Manages game projects, builds, and user data using Supabase
"""

from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Supabase database manager for Gamora AI"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[Client] = None
    
    async def connect(self):
        """Create Supabase client"""
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("✅ Connected to Supabase")
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Cleanup connection"""
        self.client = None
        logger.info("🛑 Database disconnected")
    
    async def is_healthy(self) -> bool:
        """Health check"""
        try:
            if self.client:
                # Try a simple query
                result = self.client.table('projects').select('id').limit(1).execute()
                return True
            return False
        except:
            return False
    
    async def create_tables(self):
        """Create database schema - Run this SQL in Supabase SQL Editor"""
        logger.info("ℹ️  Please run the SQL schema in Supabase SQL Editor (see core/supabase_schema.sql)")
        # Tables are created via Supabase SQL Editor, not programmatically
        # This is a placeholder to maintain compatibility
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            projects_count = self.client.table('projects').select('id', count='exact').execute()
            builds_count = self.client.table('game_builds').select('id', count='exact').execute()
            
            return {
                'total_projects': projects_count.count or 0,
                'total_builds': builds_count.count or 0,
                'total_users': 0  # Users managed by Supabase Auth
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {'total_projects': 0, 'total_builds': 0, 'total_users': 0}
    
    # Project operations
    async def create_project(
        self,
        project_id: str,
        user_id: str,  # Supabase user UUID
        title: str,
        prompt: str,
        **kwargs
    ) -> Dict:
        """Create new project"""
        try:
            data = {
                'id': project_id,
                'user_id': user_id,
                'title': title,
                'prompt': prompt,
                'description': kwargs.get('description'),
                'genre': kwargs.get('genre'),
                'status': 'generating',
                'metadata': kwargs.get('metadata', {}),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('projects').insert(data).execute()
            return result.data[0] if result.data else data
        except Exception as e:
            logger.error(f"Create project error: {e}")
            raise
    
    async def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        try:
            result = self.client.table('projects').select('*').eq('id', project_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Get project error: {e}")
            return None
    
    async def update_project(
        self,
        project_id: str,
        **updates
    ) -> bool:
        """Update project"""
        if not updates:
            return False
        
        try:
            # Convert datetime objects to ISO strings and remove non-serializable data
            def clean_value(v):
                if isinstance(v, datetime):
                    return v.isoformat()
                elif isinstance(v, bytes):
                    # Skip binary data - it should be stored separately
                    return None
                elif isinstance(v, dict):
                    # Recursively clean dict values
                    return {k: clean_value(val) for k, val in v.items() if clean_value(val) is not None}
                elif isinstance(v, list):
                    # Clean list items
                    return [clean_value(item) for item in v if clean_value(item) is not None]
                else:
                    return v
            
            update_data = {}
            for key, value in updates.items():
                cleaned = clean_value(value)
                if cleaned is not None:
                    update_data[key] = cleaned
            
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.client.table('projects').update(update_data).eq('id', project_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Update project error: {e}")
            return False
    
    async def get_user_projects(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Get projects for a user"""
        try:
            result = self.client.table('projects')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get user projects error: {e}")
            return []
    
    async def list_projects(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """List projects with filters"""
        try:
            query = self.client.table('projects').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            if status:
                query = query.eq('status', status)
            
            result = query.order('created_at', desc=True).limit(limit).offset(offset).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"List projects error: {e}")
            return []
    
    # Build operations
    async def create_build(
        self,
        project_id: str,
        platform: str,
        build_url: str,
        **kwargs
    ) -> str:
        """Create build record"""
        try:
            data = {
                'project_id': project_id,
                'platform': platform,
                'build_url': build_url,
                'web_preview_url': kwargs.get('web_preview_url'),
                'file_size': kwargs.get('file_size'),
                'version': kwargs.get('version', '1.0.0'),
                'status': kwargs.get('status', 'completed'),
                'metadata': kwargs.get('metadata', {}),
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('game_builds').insert(data).execute()
            return result.data[0]['id'] if result.data else ''
        except Exception as e:
            logger.error(f"Create build error: {e}")
            raise
    
    async def get_builds(self, project_id: str) -> List[Dict]:
        """Get all builds for a project"""
        try:
            result = self.client.table('game_builds')\
                .select('*')\
                .eq('project_id', project_id)\
                .order('created_at', desc=False)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get builds error: {e}")
            return []
    
    async def update_build(self, build_id: str, **updates) -> bool:
        """Update build record"""
        if not updates:
            return False
        
        try:
            result = self.client.table('game_builds').update(updates).eq('id', build_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Update build error: {e}")
            return False
    
    # Log operations
    async def log_generation_step(
        self,
        project_id: str,
        step: str,
        status: str,
        **kwargs
    ):
        """Log a generation step"""
        try:
            data = {
                'project_id': project_id,
                'step': step,
                'status': status,
                'duration_ms': kwargs.get('duration_ms'),
                'ai_model': kwargs.get('ai_model'),
                'tokens_used': kwargs.get('tokens_used'),
                'error': kwargs.get('error'),
                'metadata': kwargs.get('metadata', {}),
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.client.table('generation_logs').insert(data).execute()
        except Exception as e:
            logger.error(f"Log generation step error: {e}")
    
    async def get_project_logs(self, project_id: str) -> List[Dict]:
        """Get all logs for a project"""
        try:
            result = self.client.table('generation_logs')\
                .select('*')\
                .eq('project_id', project_id)\
                .order('created_at', desc=False)\
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Get project logs error: {e}")
            return []
