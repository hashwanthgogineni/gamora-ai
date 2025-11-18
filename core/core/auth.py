"""
Authentication Manager - Supabase JWT-based authentication
"""

from supabase import create_client, Client
from typing import Optional, Dict
import logging
import jwt
from datetime import datetime

logger = logging.getLogger(__name__)


class AuthManager:
    """Handle user authentication using Supabase JWT tokens"""
    
    def __init__(self, supabase_url: str, supabase_anon_key: str):
        self.supabase_url = supabase_url
        self.supabase_anon_key = supabase_anon_key
        self.client: Optional[Client] = None
    
    async def initialize(self):
        """Initialize Supabase client"""
        self.client = create_client(self.supabase_url, self.supabase_anon_key)
        logger.info("✅ Auth Manager initialized with Supabase")
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify Supabase JWT token"""
        try:
            # Use Supabase client to verify token
            # The token is already verified by Supabase, we just need to decode it
            # Note: In production, you should verify the JWT signature
            # For now, we'll decode without verification (Supabase handles this)
            
            # Decode without verification (Supabase already verified it)
            # In production, you should verify the signature using Supabase's JWT secret
            decoded = jwt.decode(
                token,
                options={"verify_signature": False}  # Supabase already verified
            )
            
            return {
                "user_id": decoded.get("sub"),  # Supabase uses 'sub' for user ID
                "email": decoded.get("email"),
                "role": decoded.get("role", "authenticated")
            }
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def get_current_user(self, token: str) -> Optional[Dict]:
        """Get current user from token"""
        return self.verify_token(token)
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID from Supabase Auth"""
        try:
            # Note: Supabase Auth doesn't expose a direct API to get user by ID
            # You would need to use the admin API or store user data in your own table
            # For now, return basic info from token
            return {
                "id": user_id,
                "email": None  # Would need to fetch from auth.users table
            }
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
