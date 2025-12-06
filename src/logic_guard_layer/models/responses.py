"""API response models for Logic-Guard-Layer."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ViolationType(str, Enum):
    """Types of constraint violations."""
    TYPE_ERROR = "TYPE_ERROR"
    RANGE_ERROR = "RANGE_ERROR"
    RELATIONAL_ERROR = "RELATIONAL_ERROR"
    TEMPORAL_ERROR = "TEMPORAL_ERROR"
    PHYSICAL_ERROR = "PHYSICAL_ERROR"
    PARSE_ERROR = "PARSE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class Violation(BaseModel):
    """A constraint violation detected during validation."""
    type: ViolationType = Field(..., description="Type of violation")
    constraint: str = Field(..., description="The constraint that was violated")
    message: str = Field(..., description="Human-readable error message")
    entity: Optional[str] = Field(None, description="The entity that caused the violation")
    property_name: Optional[str] = Field(None, description="The property that caused the violation")
    actual_value: Optional[Any] = Field(None, description="The actual value found")
    expected_value: Optional[Any] = Field(None, description="The expected value or range")
    severity: str = Field(default="error", description="Severity level (error, warning)")

    def __str__(self) -> str:
        return f"[{self.type.value}] {self.message}"


class IterationInfo(BaseModel):
    """Information about a single correction iteration."""
    number: int = Field(..., description="Iteration number (1-based)")
    violations_count: int = Field(..., description="Number of violations in this iteration")
    corrected_text: Optional[str] = Field(None, description="Text after correction attempt")


class ValidationResult(BaseModel):
    """Result of a validation operation."""
    success: bool = Field(..., description="Whether validation succeeded")
    data: Optional[dict[str, Any]] = Field(None, description="Extracted structured data")
    violations: list[Violation] = Field(default_factory=list, description="List of violations found")
    iterations: int = Field(default=1, description="Number of correction iterations performed")
    iteration_history: list[IterationInfo] = Field(default_factory=list, description="History of iterations")
    checked_constraints: int = Field(default=0, description="Number of constraints checked")
    processing_time_ms: float = Field(default=0.0, description="Processing time in milliseconds")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    original_text: Optional[str] = Field(None, description="The original input text")
    corrected_text: Optional[str] = Field(None, description="The corrected text (if corrections were made)")
    error: Optional[str] = Field(None, description="Error message if validation failed catastrophically")

    @property
    def violations_count(self) -> int:
        """Get the number of violations."""
        return len(self.violations)

    def to_summary(self) -> str:
        """Generate a human-readable summary."""
        if self.success:
            return f"Validation PASSED ({self.iterations} iteration(s), {self.checked_constraints} constraints checked)"
        else:
            return f"Validation FAILED: {self.violations_count} violation(s) found after {self.iterations} iteration(s)"


class ValidationRequest(BaseModel):
    """Request model for validation endpoint."""
    text: str = Field(..., min_length=1, description="The text to validate")
    schema_name: str = Field(default="maintenance", description="The schema/domain to use")
    max_iterations: Optional[int] = Field(None, ge=1, le=10, description="Override max iterations")


class ValidationResponse(BaseModel):
    """Response model for validation endpoint."""
    success: bool
    data: Optional[dict[str, Any]] = None
    violations: list[dict[str, Any]] = Field(default_factory=list)
    iterations: int = 1
    checked_constraints: int = 0
    processing_time_ms: float = 0.0
    confidence: float = 1.0
    error: Optional[str] = None

    @classmethod
    def from_result(cls, result: ValidationResult) -> "ValidationResponse":
        """Create response from ValidationResult."""
        return cls(
            success=result.success,
            data=result.data,
            violations=[v.model_dump() for v in result.violations],
            iterations=result.iterations,
            checked_constraints=result.checked_constraints,
            processing_time_ms=result.processing_time_ms,
            confidence=result.confidence,
            error=result.error,
        )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = "healthy"
    version: str
    model: str
    ontology_loaded: bool = False


class StatsResponse(BaseModel):
    """Response model for statistics endpoint."""
    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    success_rate: float = 0.0
    avg_iterations: float = 0.0
    avg_processing_time_ms: float = 0.0
    constraints_count: int = 0
