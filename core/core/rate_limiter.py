"""
Rate Limiter - Redis-based rate limiting
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting using Redis"""
    
    def __init__(self, cache_manager):
        self.cache = cache_manager
        self.default_limit = 100  # requests per hour
        self.window = 3600  # 1 hour in seconds
    
    async def check_rate_limit(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> tuple[bool, int]:
        """
        Check if rate limit is exceeded
        
        Returns:
            (allowed: bool, remaining: int)
        """
        limit = limit or self.default_limit
        window = window or self.window
        
        redis_key = f"rate_limit:{key}"
        
        # Get current count
        count = await self.cache.get(redis_key)
        current = int(count) if count else 0
        
        # Check limit
        if current >= limit:
            return False, 0
        
        # Increment counter
        await self.cache.incr(redis_key)
        
        # Set expiry on first request
        if current == 0:
            await self.cache.expire(redis_key, window)
        
        remaining = limit - current - 1
        return True, remaining
    
    async def reset_rate_limit(self, key: str):
        """Reset rate limit for key"""
        redis_key = f"rate_limit:{key}"
        await self.cache.delete(redis_key)
        logger.info(f"Rate limit reset for {key}")
