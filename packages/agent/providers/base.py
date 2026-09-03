from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class PlannedToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""

class AgentPlan(BaseModel):
    classified_intent: str
    target_entity: Optional[str] = None
    target_entity_id: Optional[str] = None
    confidence: float = 1.0
    planned_tools: List[PlannedToolCall] = Field(default_factory=list)
    explanation: str = ""

class BaseModelProvider(ABC):
    """Abstract interface for model providers (mock, Gemini, OpenAI, Ollama)."""

    @abstractmethod
    async def classify_intent(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Classify user query into intent, entities, and risk level."""
        pass

    @abstractmethod
    async def generate_plan(
        self,
        query: str,
        persona: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AgentPlan:
        """Generate structured tool execution plan."""
        pass
