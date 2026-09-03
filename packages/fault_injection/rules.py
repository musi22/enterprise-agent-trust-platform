from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class FaultType(str, Enum):
    HTTP_401 = "HTTP_401"
    HTTP_403 = "HTTP_403"
    HTTP_429 = "HTTP_429"
    HTTP_500 = "HTTP_500"
    TIMEOUT = "TIMEOUT"
    DELAYED_RESPONSE = "DELAYED_RESPONSE"
    MALFORMED_ARGUMENTS = "MALFORMED_ARGUMENTS"
    MALFORMED_TOOL_RESPONSE = "MALFORMED_TOOL_RESPONSE"
    STALE_INVENTORY = "STALE_INVENTORY"
    PRICE_CHANGE = "PRICE_CHANGE"
    DUPLICATE_EVENT_DELIVERY = "DUPLICATE_EVENT_DELIVERY"
    PARTIAL_DB_FAILURE = "PARTIAL_DB_FAILURE"
    SILENT_WRONG_IDENTIFIER = "SILENT_WRONG_IDENTIFIER"
    EMPTY_RESULT = "EMPTY_RESULT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

class FaultConfig(BaseModel):
    fault_type: FaultType
    target_tool: str = "*"  # Tool name or wildcard
    probability: float = 1.0
    invocation_count: Optional[int] = 1  # Strike on the Nth invocation (1-based), None for always
    seed: int = 42
    delay_seconds: float = 0.5
    activation_rule: Optional[Dict[str, Any]] = None
    expected_recovery_behavior: Optional[str] = None
    custom_payload: Optional[Dict[str, Any]] = None

class InjectedFaultException(Exception):
    def __init__(self, fault_type: FaultType, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.fault_type = fault_type
        self.status_code = status_code
        self.details = details or {}
