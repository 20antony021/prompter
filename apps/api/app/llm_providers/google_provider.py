"""Google Gemini LLM provider."""
import logging
from typing import Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.llm_providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model_name: str = "gemini-pro"):
        """
        Initialize Google provider.

        Args:
            api_key: Google API key
            model_name: Model name (default: gemini-pro)
        """
        super().__init__(api_key, model_name)
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

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
        Generate response from Google Gemini.

        Args:
            prompt: User prompt
            system_prompt: System prompt (combined with user prompt for Gemini)
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            LLM response
        """
        try:
            # Combine system and user prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Configure generation
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
            )

            return LLMResponse(
                text=response.text,
                model=self.model_name,
                provider=self.provider_name,
                tokens_used=None,  # Gemini doesn't provide token counts in the same way
                finish_reason=str(response.candidates[0].finish_reason)
                if response.candidates
                else None,
                raw_response={
                    "text": response.text,
                    "candidates": [c.to_dict() for c in response.candidates]
                    if response.candidates
                    else [],
                },
            )

        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            raise

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "google"

