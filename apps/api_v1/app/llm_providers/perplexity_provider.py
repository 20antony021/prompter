"""Perplexity AI LLM provider."""
import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.llm_providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class PerplexityProvider(BaseLLMProvider):
    """Perplexity AI API provider."""

    def __init__(self, api_key: str, model_name: str = "llama-3.1-sonar-large-128k-online"):
        """
        Initialize Perplexity provider.

        Args:
            api_key: Perplexity API key
            model_name: Model name (default: llama-3.1-sonar-large-128k-online)
        """
        super().__init__(api_key, model_name)
        self.api_url = "https://api.perplexity.ai/chat/completions"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """
        Generate response from Perplexity AI.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            LLM response
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            # Extract response text
            text = data["choices"][0]["message"]["content"]
            
            # Extract usage info
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens")

            return LLMResponse(
                text=text,
                model=self.model_name,
                provider=self.provider_name,
                tokens_used=tokens_used,
                finish_reason=data["choices"][0].get("finish_reason"),
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            raise

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "perplexity"

