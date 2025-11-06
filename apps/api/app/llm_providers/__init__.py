"""LLM provider factory and utilities."""
from typing import Dict, Type

from app.config import settings
from app.llm_providers.base import BaseLLMProvider, LLMResponse
from app.llm_providers.google_provider import GoogleProvider
from app.llm_providers.openai_provider import OpenAIProvider
from app.llm_providers.perplexity_provider import PerplexityProvider

__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "OpenAIProvider",
    "PerplexityProvider",
    "GoogleProvider",
    "get_provider",
    "get_all_providers",
]

# Model configurations
MODEL_CONFIGS: Dict[str, Dict[str, str]] = {
    "gpt-4": {"provider": "openai", "model": "gpt-4-turbo-preview"},
    "gpt-3.5": {"provider": "openai", "model": "gpt-3.5-turbo"},
    "perplexity-sonar": {"provider": "perplexity", "model": "llama-3.1-sonar-large-128k-online"},
    "perplexity-sonar-small": {"provider": "perplexity", "model": "llama-3.1-sonar-small-128k-online"},
    "gemini-pro": {"provider": "google", "model": "gemini-pro"},
}

# Provider classes
PROVIDER_CLASSES: Dict[str, Type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "perplexity": PerplexityProvider,
    "google": GoogleProvider,
}


def get_provider(model_key: str) -> BaseLLMProvider:
    """
    Get LLM provider instance for a model.

    Args:
        model_key: Model key (e.g., "gpt-4", "claude-3-opus")

    Returns:
        Initialized provider instance

    Raises:
        ValueError: If model key is not found
    """
    if model_key not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model key: {model_key}")

    config = MODEL_CONFIGS[model_key]
    provider_name = config["provider"]
    model_name = config["model"]

    provider_class = PROVIDER_CLASSES[provider_name]

    # Get API key based on provider
    if provider_name == "openai":
        api_key = settings.OPENAI_API_KEY
    elif provider_name == "perplexity":
        api_key = settings.PERPLEXITY_API_KEY
    elif provider_name == "google":
        api_key = settings.GOOGLE_GENAI_API_KEY
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    return provider_class(api_key=api_key, model_name=model_name)


def get_all_providers() -> Dict[str, BaseLLMProvider]:
    """
    Get all configured LLM providers.

    Returns:
        Dictionary mapping model keys to provider instances
    """
    providers = {}
    for model_key in MODEL_CONFIGS:
        try:
            providers[model_key] = get_provider(model_key)
        except Exception as e:
            import logging

            logging.warning(f"Could not initialize provider for {model_key}: {e}")
    return providers

