"""
Supabase Storage Service
Handles file uploads for game builds, assets, and previews
"""

import os
from typing import Optional, Dict, Any
import logging
from supabase import create_client, Client
from datetime import datetime, timedelta
import mimetypes

logger = logging.getLogger(__name__)


class StorageService:
    """
    Supabase storage integration
    Manages game builds, assets, and web previews
    """
    
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        bucket: str = "gamoraai-projects"
    ):
        """Initialize with Supabase storage"""
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.bucket = bucket
        self.client: Optional[Client] = None
        logger.info(f"📦 Storage Service configured for Supabase")
    
    async def connect(self):
        """Initialize storage connection"""
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            
            # Ensure bucket exists
            try:
                buckets = self.client.storage.list_buckets()
                # Handle both dict and object responses
                bucket_names = []
                if buckets:
                    if isinstance(buckets, list):
                        for b in buckets:
                            if isinstance(b, dict):
                                bucket_names.append(b.get('name', ''))
                            else:
                                bucket_names.append(getattr(b, 'name', getattr(b, 'id', str(b))))
                    elif hasattr(buckets, '__iter__'):
                        bucket_names = [getattr(b, 'name', getattr(b, 'id', str(b))) for b in buckets]
                
                logger.info(f"📦 Found buckets: {bucket_names}")
                
                if self.bucket not in bucket_names:
                    logger.info(f"📦 Creating bucket: {self.bucket}")
                    try:
                        result = self.client.storage.create_bucket(
                            self.bucket,
                            options={"public": False}
                        )
                        logger.info(f"✅ Created Supabase bucket: {self.bucket}")
                    except Exception as create_error:
                        logger.error(f"❌ Failed to create bucket: {create_error}")
                        # Try to continue anyway - bucket might exist but not in list
                        logger.warning(f"⚠️  Continuing without bucket creation - check Supabase dashboard")
                else:
                    logger.info(f"✅ Bucket exists: {self.bucket}")
            except Exception as e:
                logger.error(f"❌ Bucket check/creation failed: {e}")
                logger.warning(f"⚠️  Make sure bucket '{self.bucket}' exists in Supabase Storage dashboard")
            
            logger.info("✅ Connected to Supabase Storage")
                
        except Exception as e:
            logger.error(f"❌ Storage connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Cleanup storage connection"""
        self.client = None
        logger.info("🛑 Storage service disconnected")
    
    async def is_healthy(self) -> bool:
        """Health check"""
        try:
            if self.client:
                # Try to list buckets
                self.client.storage.list_buckets()
                return True
            return False
        except:
            return False
    
    async def upload_file(
        self,
        path: str,
        data: bytes,
        content_type: str = 'application/octet-stream',
        public: bool = False,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload file to storage
        
        Args:
            path: Storage path (e.g., "games/project-123/web/game.html")
            data: File data as bytes
            content_type: MIME type
            public: Make file publicly accessible
            metadata: Additional metadata
        
        Returns:
            Public URL or signed URL
        """
        try:
            # Verify bucket exists before upload
            try:
                buckets = self.client.storage.list_buckets()
                bucket_exists = False
                if buckets:
                    if isinstance(buckets, list):
                        bucket_exists = any(
                            (isinstance(b, dict) and b.get('name') == self.bucket) or 
                            (hasattr(b, 'name') and getattr(b, 'name') == self.bucket)
                            for b in buckets
                        )
                    else:
                        bucket_exists = any(
                            getattr(b, 'name', None) == self.bucket for b in buckets
                        )
                
                if not bucket_exists:
                    logger.error(f"❌ Bucket '{self.bucket}' does not exist! Please create it in Supabase Storage dashboard.")
                    raise Exception(f"Bucket '{self.bucket}' not found. Create it in Supabase Storage first.")
            except Exception as check_error:
                logger.warning(f"⚠️  Could not verify bucket existence: {check_error}")
            
            # Upload to Supabase with proper file options
            file_options = {
                "content-type": content_type,
                "upsert": "true",
                "cache-control": "public, max-age=3600"
            }
            
            # For HTML files, ensure they're served correctly
            if content_type == 'text/html':
                file_options["content-disposition"] = "inline"
            
            result = self.client.storage.from_(self.bucket).upload(
                path,
                data,
                file_options
            )
            
            if public:
                # Get public URL
                url = self.client.storage.from_(self.bucket).get_public_url(path)
                logger.info(f"🌐 Public URL generated: {url}")
            else:
                # Get signed URL (expires in 1 hour)
                url = self.client.storage.from_(self.bucket).create_signed_url(
                    path,
                    3600  # 1 hour
                )['signedURL']
                logger.info(f"🔐 Signed URL generated: {url[:50]}...")
            
            logger.info(f"✅ Uploaded: {path} -> {url}")
            return url
                    
        except Exception as e:
            logger.error(f"❌ Upload failed for {path}: {e}")
            raise
    
    async def download_file(self, path: str) -> bytes:
        """Download file from storage"""
        try:
            result = self.client.storage.from_(self.bucket).download(path)
            return result
        except Exception as e:
            logger.error(f"❌ Download failed for {path}: {e}")
            raise
    
    async def delete_file(self, path: str) -> bool:
        """Delete file from storage"""
        try:
            self.client.storage.from_(self.bucket).remove([path])
            logger.info(f"🗑️ Deleted: {path}")
            return True
        except Exception as e:
            logger.error(f"❌ Delete failed for {path}: {e}")
            return False
    
    async def list_files(self, prefix: str = "") -> list:
        """List files in storage with optional prefix"""
        try:
            result = self.client.storage.from_(self.bucket).list(prefix)
            return result
        except Exception as e:
            logger.error(f"❌ List failed for prefix {prefix}: {e}")
            return []
    
    async def get_file_url(
        self,
        path: str,
        public: bool = False,
        expires_in: int = 3600
    ) -> str:
        """Get URL for file (public or signed)"""
        try:
            if public:
                return self.client.storage.from_(self.bucket).get_public_url(path)
            else:
                result = self.client.storage.from_(self.bucket).create_signed_url(
                    path,
                    expires_in
                )
                return result['signedURL']
        except Exception as e:
            logger.error(f"❌ Get URL failed for {path}: {e}")
            raise
    
    async def upload_game_build(
        self,
        project_id: str,
        platform: str,
        build_data: bytes,
        filename: str
    ) -> str:
        """Upload a game build"""
        path = f"games/{project_id}/builds/{platform}/{filename}"
        content_type = self._guess_content_type(filename)
        
        return await self.upload_file(
            path,
            build_data,
            content_type=content_type,
            metadata={
                'project_id': project_id,
                'platform': platform,
                'uploaded_at': datetime.utcnow().isoformat()
            }
        )
    
    async def upload_game_asset(
        self,
        project_id: str,
        asset_type: str,
        asset_data: bytes,
        filename: str
    ) -> str:
        """Upload a game asset"""
        path = f"games/{project_id}/assets/{asset_type}/{filename}"
        content_type = self._guess_content_type(filename)
        
        return await self.upload_file(
            path,
            asset_data,
            content_type=content_type,
            public=True
        )
    
    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
