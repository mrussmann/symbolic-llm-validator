"""Logic-Guard-Layer: Neuro-symbolic LLM output validation."""

__version__ = "1.0.0"
__author__ = "Logic-Guard-Layer Team"

from logic_guard_layer.core.orchestrator import Orchestrator, get_orchestrator
from logic_guard_layer.models.responses import ValidationResult, Violation

# Alias for backwards compatibility
LogicGuardLayer = Orchestrator

__all__ = [
    "Orchestrator",
    "LogicGuardLayer",
    "get_orchestrator",
    "ValidationResult",
    "Violation",
    "__version__",
]
