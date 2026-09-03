from typing import Optional
from packages.agent.providers.base import BaseModelProvider
from packages.agent.providers.deterministic_mock import DeterministicMockProvider
from apps.api.app.core.config import settings

def get_model_provider(provider_name: Optional[str] = None) -> BaseModelProvider:
    """Factory to instantiate configured model provider."""
    name = (provider_name or settings.DEFAULT_MODEL_PROVIDER).lower()
    
    if name in ("deterministic_mock", "mock", "local"):
        return DeterministicMockProvider()
    
    # Optional providers can fallback to mock if unconfigured
    return DeterministicMockProvider()
