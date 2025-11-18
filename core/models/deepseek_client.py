
"""
DeepSeek R1 API Client  
Specialized for code generation and logical reasoning
"""
import httpx
from typing import Dict, List, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek R1 API client optimized for code generation"""
    
    BASE_URL = "https://api.deepseek.com/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=300.0
        )
        self.model = "deepseek-reasoner"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.3,  # Lower for code
        **kwargs
    ) -> Dict[str, Any]:
        """Generate code with DeepSeek R1"""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            
            return {
                "content": choice["message"]["content"],
                "reasoning": choice["message"].get("reasoning_content", ""),
                "model": data["model"],
                "tokens_used": data["usage"]["total_tokens"],
                "finish_reason": choice["finish_reason"]
            }
        except httpx.HTTPError as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check API health"""
        try:
            await self.generate(
                messages=[{"role": "user", "content": "print('test')"}],
                max_tokens=10
            )
            return True
        except:
            return False
    
    async def close(self):
        """Cleanup"""
        await self.client.aclose()
