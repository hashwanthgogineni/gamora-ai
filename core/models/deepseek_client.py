import httpx
from typing import Dict, List, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)


class DeepSeekClient:
    # DeepSeek API client for code generation
    BASE_URL = "https://api.deepseek.com/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(300.0, connect=30.0),  # 5 min total, 30s connect
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        # Use deepseek-chat for code generation (faster, more reliable)
        # deepseek-reasoner is better for complex reasoning, but slower and can be overkill for code
        self.model = "deepseek-chat"  # Changed from deepseek-reasoner for better code generation
    
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
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
            # Use longer timeout for large responses
            response = await self.client.post(
                "/chat/completions", 
                json=payload,
                timeout=httpx.Timeout(300.0, connect=30.0)  # 5 min total, 30s connect
            )
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            
            # Handle both reasoner and chat models
            message_content = choice["message"].get("content", "")
            reasoning_content = choice["message"].get("reasoning_content", "")
            
            # For reasoner model, prefer content over reasoning for code generation
            # For chat model, content is the main output
            if not message_content and reasoning_content:
                # Fallback: use reasoning if content is empty (shouldn't happen with chat model)
                message_content = reasoning_content
                logger.warning("⚠️  Using reasoning content as main content (unusual)")
            
            if not message_content:
                logger.error("❌ Empty response from DeepSeek API")
                raise ValueError("Empty response from DeepSeek API")
            
            return {
                "content": message_content,
                "reasoning": reasoning_content,
                "model": data["model"],
                "tokens_used": data["usage"]["total_tokens"],
                "finish_reason": choice["finish_reason"]
            }
        except httpx.HTTPStatusError as e:
            # Better error handling for 400 errors
            error_detail = ""
            status_code = e.response.status_code if e.response else None
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    error_detail = f" - {error_data.get('error', {}).get('message', '')}"
                except:
                    error_detail = f" - {e.response.text[:200]}"
            
            # Log detailed error information
            logger.error(f"DeepSeek API error (Status {status_code}): {e}{error_detail}")
            
            # Log payload size for debugging
            import json as json_lib
            payload_size = len(json_lib.dumps(payload))
            if payload_size > 100000:  # > 100KB
                logger.warning(f"⚠️  Large payload size: {payload_size} bytes - may cause 400 errors")
            
            # Check for common issues
            if status_code == 401:
                logger.error("❌ DeepSeek API key is invalid or missing. Check DEEPSEEK_API_KEY environment variable.")
            elif status_code == 429:
                logger.error("❌ DeepSeek API rate limit exceeded. Please wait before retrying.")
            elif status_code == 400:
                logger.error("❌ DeepSeek API bad request. Check model name and payload format.")
            
            raise
        except httpx.HTTPError as e:
            error_msg = str(e)
            logger.error(f"DeepSeek API connection error: {e}")
            
            # Check for specific connection issues
            if "incomplete chunked read" in error_msg or "peer closed connection" in error_msg:
                logger.warning("⚠️  Connection closed prematurely - this is often a transient network issue")
                logger.info("   The system will automatically retry (up to 3 times)")
                logger.info("   If this persists, check your internet connection or DeepSeek API status")
            elif "timeout" in error_msg.lower():
                logger.warning("⚠️  Request timed out - DeepSeek may be processing a large response")
                logger.info("   The system will automatically retry with longer timeout")
            else:
                logger.error("   This could be a network issue or API endpoint problem.")
            
            # Re-raise to trigger retry
            raise
        except Exception as e:
            logger.error(f"DeepSeek API unexpected error: {e}", exc_info=True)
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
