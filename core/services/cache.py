"""
In-Memory Cache Service
Provides caching for AI responses and rate limiting
Note: For production, consider using Supabase Realtime or Redis
"""

from typing import Optional, Any, Dict
import json
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class CacheManager:
    """In-memory cache manager for Gamora AI"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()
        logger.info("✅ Cache Manager initialized (in-memory)")
    
    async def connect(self):
        """Initialize cache (no-op for in-memory)"""
        logger.info("✅ Cache connected")
    
    async def disconnect(self):
        """Cleanup cache"""
        self.cache.clear()
        logger.info("🛑 Cache disconnected")
    
    async def is_healthy(self) -> bool:
        """Health check"""
        return True
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        async with self.lock:
            return {
                'total_keys': len(self.cache),
                'keyspace_hits': 0,  # Not tracked in simple implementation
                'keyspace_misses': 0,
                'connected_clients': 1
            }
    
    # Basic cache operations
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                # Check expiration
                if 'expires_at' in entry:
                    if datetime.utcnow() > entry['expires_at']:
                        del self.cache[key]
                        return None
                return entry.get('value')
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: int = 3600
    ) -> bool:
        """Set value in cache with expiration"""
        async with self.lock:
            expires_at = datetime.utcnow() + timedelta(seconds=expire)
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.utcnow()
            }
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter in cache (Redis-like behavior)"""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                # Check expiration
                if 'expires_at' in entry:
                    if datetime.utcnow() > entry['expires_at']:
                        # Expired, reset to amount with new expiration
                        expires_at = datetime.utcnow() + timedelta(seconds=3600)
                        self.cache[key] = {
                            'value': amount,
                            'expires_at': expires_at,
                            'created_at': datetime.utcnow()
                        }
                        return amount
                
                current = entry.get('value', 0)
                if isinstance(current, (int, float)):
                    new_value = int(current) + amount
                else:
                    new_value = amount
                
                # Preserve expiration
                expires_at = entry.get('expires_at')
                self.cache[key] = {
                    'value': new_value,
                    'expires_at': expires_at,
                    'created_at': entry.get('created_at', datetime.utcnow())
                }
                return new_value
            else:
                # Key doesn't exist, create it
                expires_at = datetime.utcnow() + timedelta(seconds=3600)
                self.cache[key] = {
                    'value': amount,
                    'expires_at': expires_at,
                    'created_at': datetime.utcnow()
                }
                return amount
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key (Redis-like behavior)"""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                expires_at = datetime.utcnow() + timedelta(seconds=seconds)
                self.cache[key] = {
                    'value': entry.get('value'),
                    'expires_at': expires_at,
                    'created_at': entry.get('created_at', datetime.utcnow())
                }
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                # Check expiration
                if 'expires_at' in entry:
                    if datetime.utcnow() > entry['expires_at']:
                        del self.cache[key]
                        return False
                return True
            return False
    
    # AI-specific caching
    async def cache_ai_response(
        self,
        prompt_hash: str,
        response: dict,
        expire: int = 86400  # 24 hours
    ):
        """Cache AI model response"""
        key = f"ai_response:{prompt_hash}"
        await self.set(key, response, expire)
    
    async def get_cached_ai_response(
        self,
        prompt_hash: str
    ) -> Optional[dict]:
        """Get cached AI response"""
        key = f"ai_response:{prompt_hash}"
        return await self.get(key)
    
    # Rate limiting
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int = 10,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check rate limit for identifier
        
        Returns:
            (allowed, remaining_requests)
        """
        key = f"rate_limit:{identifier}"
        
        async with self.lock:
            entry = await self.get(key)
            
            if entry is None:
                # First request in window
                await self.set(key, 1, window)
                return True, limit - 1
            
            current = entry if isinstance(entry, int) else entry.get('value', 0)
            
            if current >= limit:
                # Limit exceeded
                return False, 0
            
            # Increment counter
            expires_at = datetime.utcnow() + timedelta(seconds=window)
            self.cache[key] = {
                'value': current + 1,
                'expires_at': expires_at,
                'created_at': self.cache.get(key, {}).get('created_at', datetime.utcnow())
            }
            return True, limit - current - 1
    
    async def reset_rate_limit(self, identifier: str):
        """Reset rate limit for identifier"""
        key = f"rate_limit:{identifier}"
        await self.delete(key)
    
    # Session management
    async def set_session(
        self,
        session_id: str,
        data: dict,
        expire: int = 3600
    ):
        """Store session data"""
        key = f"session:{session_id}"
        await self.set(key, data, expire)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def delete_session(self, session_id: str):
        """Delete session"""
        key = f"session:{session_id}"
        await self.delete(key)
    
    # Project-specific caching
    async def cache_project_data(
        self,
        project_id: str,
        data: dict,
        expire: int = 3600
    ):
        """Cache project data"""
        key = f"project:{project_id}"
        await self.set(key, data, expire)
    
    async def get_cached_project(self, project_id: str) -> Optional[dict]:
        """Get cached project data"""
        key = f"project:{project_id}"
        return await self.get(key)
    
    async def invalidate_project_cache(self, project_id: str):
        """Invalidate project cache"""
        key = f"project:{project_id}"
        await self.delete(key)
    
    # Generation status tracking
    async def set_generation_status(
        self,
        project_id: str,
        status: dict
    ):
        """Set generation status"""
        key = f"gen_status:{project_id}"
        await self.set(key, status, expire=7200)  # 2 hours
    
    async def get_generation_status(
        self,
        project_id: str
    ) -> Optional[dict]:
        """Get generation status"""
        key = f"gen_status:{project_id}"
        return await self.get(key)
    
    # Pub/Sub for real-time updates (not implemented for in-memory)
    async def publish_update(
        self,
        channel: str,
        message: dict
    ):
        """Publish update to channel (no-op for in-memory)"""
        logger.debug(f"Publish to {channel}: {message}")
        # In-memory cache doesn't support pub/sub
        # Use WebSocket manager for real-time updates
    
    async def subscribe_to_updates(self, channel: str):
        """Subscribe to update channel (not implemented)"""
        # Not implemented for in-memory cache
        return None
