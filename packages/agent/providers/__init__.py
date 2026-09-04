from typing import Optional
from packages.agent.providers.base import BaseModelProvider
from packages.agent.providers.deterministic_mock import DeterministicMockProvider
from packages.agent.providers.gemini_provider import GeminiProvider
from apps.api.app.core.config import settings

def get_model_provider(provider_name: Optional[str] = None) -> BaseModelProvider:
    """Factory to instantiate configured model provider."""
    name = (provider_name or settings.DEFAULT_MODEL_PROVIDER).lower()
    
    if name in ("deterministic_mock", "mock", "local"):
        return DeterministicMockProvider()
    elif name in ("gemini", "google"):
        return GeminiProvider(api_key=settings.GEMINI_API_KEY)
    
    # Optional providers fallback to mock if unconfigured
    return DeterministicMockProvider()

