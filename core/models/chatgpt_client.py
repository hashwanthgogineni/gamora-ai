
"""
ChatGPT-4 Turbo API Client
Primary model for creative tasks, design, and complex reasoning
"""
import asyncio
from openai import AsyncOpenAI
from typing import Dict, List, Any, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ChatGPTClient:
    """ChatGPT-4 Turbo client with retry logic and fallback"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.primary_model = "gpt-4-turbo-preview"  # Most capable
        self.fallback_model = "gpt-4o-mini"  # Fast fallback
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        use_fallback: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion with ChatGPT-4 Turbo
        
        Args:
            messages: Chat messages
            max_tokens: Max tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            use_fallback: Use faster GPT-4o-mini model
        
        Returns:
            Response with content and metadata
        """
        model = self.fallback_model if use_fallback else self.primary_model
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": model,
                "tokens_used": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"ChatGPT API error: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ):
        """Stream completion"""
        try:
            stream = await self.client.chat.completions.create(
                model=self.primary_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"content": chunk.choices[0].delta.content}
                    
        except Exception as e:
            logger.error(f"ChatGPT streaming error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check API health"""
        try:
            await self.generate(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            return True
        except:
            return False
    
    async def close(self):
        """Cleanup"""
        await self.client.close()
