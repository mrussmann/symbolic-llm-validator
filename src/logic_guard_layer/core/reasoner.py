"""Reasoning module for constraint validation."""

import logging
import time
from typing import Any, Optional

from logic_guard_layer.models.responses import Violation, ViolationType
from logic_guard_layer.ontology.constraints import (
    MAINTENANCE_CONSTRAINTS,
    Constraint,
    get_all_constraints,
)

logger = logging.getLogger(__name__)


class ConsistencyResult:
    """Result of a consistency check."""

    def __init__(
        self,
        is_consistent: bool,
        violations: list[Violation],
        checked_constraints: int,
        processing_time_ms: float,
    ):
        self.is_consistent = is_consistent
        self.violations = violations
        self.checked_constraints = checked_constraints
        self.processing_time_ms = processing_time_ms

    def __str__(self) -> str:
        if self.is_consistent:
            return f"Consistent ({self.checked_constraints} constraints checked)"
        return f"Inconsistent: {len(self.violations)} violations found"


class ReasoningModule:
    """
    Reasoning module for checking data consistency against constraints.
    Uses rule-based fast checks for common constraints.
    """

    def __init__(self, constraints: Optional[list[Constraint]] = None):
        """Initialize the reasoning module.

        Args:
            constraints: List of constraints to check (uses defaults if not provided)
        """
        self.constraints = constraints or get_all_constraints()
        logger.info(f"ReasoningModule initialized with {len(self.constraints)} constraints")

    def check_consistency(self, data: dict) -> ConsistencyResult:
        """Check if data is consistent with all constraints.

        Args:
            data: Dictionary of values to check

        Returns:
            ConsistencyResult with violations list
        """
        start_time = time.time()
        violations = []
        checked = 0

        for constraint in self.constraints:
            checked += 1
            try:
                violation = constraint.check_fn(data)
                if violation is not None:
                    # Add entity info if available
                    if "name" in data:
                        violation.entity = data["name"]
                    violations.append(violation)
                    logger.debug(f"Constraint {constraint.id} violated: {violation.message}")
            except Exception as e:
                logger.warning(f"Error checking constraint {constraint.id}: {e}")

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        result = ConsistencyResult(
            is_consistent=len(violations) == 0,
            violations=violations,
            checked_constraints=checked,
            processing_time_ms=processing_time,
        )

        logger.debug(f"Consistency check: {result}")
        return result

    def check_single_constraint(
        self, constraint_id: str, data: dict
    ) -> Optional[Violation]:
        """Check a single constraint by ID.

        Args:
            constraint_id: The constraint ID (e.g., "C1")
            data: Dictionary of values to check

        Returns:
            Violation if constraint is violated, None otherwise
        """
        for constraint in self.constraints:
            if constraint.id == constraint_id:
                return constraint.check_fn(data)
        return None

    def get_applicable_constraints(self, component_type: str) -> list[Constraint]:
        """Get constraints applicable to a specific component type.

        Args:
            component_type: The component type name

        Returns:
            List of applicable constraints
        """
        return [
            c for c in self.constraints
            if component_type in c.applicable_types or "Component" in c.applicable_types
        ]

    def validate_with_ontology(self, data: dict) -> ConsistencyResult:
        """
        Validate data using OWL reasoning (for complex constraints).
        Falls back to rule-based checking if ontology is not available.

        Args:
            data: Dictionary of values to check

        Returns:
            ConsistencyResult
        """
        try:
            from logic_guard_layer.ontology.loader import get_ontology_loader

            loader = get_ontology_loader()
            if not loader.is_loaded:
                logger.warning("Ontology not loaded, using rule-based validation only")
                return self.check_consistency(data)

            # First do rule-based checks
            result = self.check_consistency(data)

            # Then try OWL reasoning for type validation
            component_type = data.get("typ") or data.get("type")
            if component_type and not loader.is_valid_type(component_type):
                result.violations.append(
                    Violation(
                        type=ViolationType.TYPE_ERROR,
                        constraint="valid_type",
                        message=f"Unknown component type: {component_type}",
                        property_name="type",
                        actual_value=component_type,
                    )
                )
                result.is_consistent = False

            return result

        except Exception as e:
            logger.warning(f"OWL validation failed, using rule-based only: {e}")
            return self.check_consistency(data)

    def get_constraints_summary(self) -> list[dict]:
        """Get a summary of all constraints for display.

        Returns:
            List of constraint summaries
        """
        return [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type.value,
                "expression": c.expression,
                "description": c.description,
            }
            for c in self.constraints
        ]
