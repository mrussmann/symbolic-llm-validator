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
        owl_violations_count: int = 0,
    ):
        self.is_consistent = is_consistent
        self.violations = violations
        self.checked_constraints = checked_constraints
        self.processing_time_ms = processing_time_ms
        self.owl_violations_count = owl_violations_count

    def __str__(self) -> str:
        if self.is_consistent:
            return f"Consistent ({self.checked_constraints} constraints checked)"
        owl_info = f", {self.owl_violations_count} from OWL" if self.owl_violations_count > 0 else ""
        return f"Inconsistent: {len(self.violations)} violations found{owl_info}"


class ReasoningModule:
    """
    Reasoning module for checking data consistency against constraints.

    Uses a hybrid approach:
    1. OWL reasoning with SWRL rules for type checking and some physics constraints
    2. Rule-based fast checks for common constraints

    The OWL-based validation provides:
    - Type hierarchy inference
    - SWRL rule-based constraint checking (cavitation, lifespan, etc.)
    - Datatype range validation via OWL restrictions

    The rule-based validation provides:
    - Fast execution for simple range checks
    - Complex physics calculations (Carnot, isentropic compression, etc.)
    """

    def __init__(
        self,
        constraints: Optional[list[Constraint]] = None,
        use_owl_reasoning: bool = True,
    ):
        """Initialize the reasoning module.

        Args:
            constraints: List of constraints to check (uses defaults if not provided)
            use_owl_reasoning: Whether to use OWL-based validation (default True)
        """
        self.constraints = constraints or get_all_constraints()
        self.use_owl_reasoning = use_owl_reasoning
        self._owl_loader = None
        logger.info(f"ReasoningModule initialized with {len(self.constraints)} constraints, OWL reasoning: {use_owl_reasoning}")

    def _get_owl_loader(self):
        """Get or initialize the OWL ontology loader."""
        if self._owl_loader is None:
            try:
                from logic_guard_layer.ontology.loader import load_ontology
                self._owl_loader = load_ontology()
            except Exception as e:
                logger.warning(f"Could not load OWL ontology: {e}")
                self._owl_loader = None
        return self._owl_loader

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
        owl_violations_count = 0

        logger.info(f"Checking consistency for data: {data}")

        # Step 1: OWL-based validation (if enabled)
        if self.use_owl_reasoning:
            owl_violations = self._check_with_owl(data)
            owl_violations_count = len(owl_violations)
            violations.extend(owl_violations)
            logger.info(f"OWL reasoning found {owl_violations_count} violations")

        # Step 2: Rule-based constraint checking
        for constraint in self.constraints:
            checked += 1
            try:
                violation = constraint.check_fn(data)
                if violation is not None:
                    # Avoid duplicate violations from OWL and rule-based checks
                    if not self._is_duplicate_violation(violation, violations):
                        # Add entity info if available
                        if "name" in data:
                            violation.entity = data["name"]
                        violations.append(violation)
                        logger.info(f"Constraint {constraint.id} ({constraint.name}) violated: {violation.message}")
            except Exception as e:
                logger.warning(f"Error checking constraint {constraint.id}: {e}")

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        result = ConsistencyResult(
            is_consistent=len(violations) == 0,
            violations=violations,
            checked_constraints=checked,
            processing_time_ms=processing_time,
            owl_violations_count=owl_violations_count,
        )

        logger.info(f"Consistency check complete: {checked} constraints checked, {len(violations)} violations found")
        return result

    def _check_with_owl(self, data: dict) -> list[Violation]:
        """Perform OWL-based validation using the ontology loader.

        Args:
            data: Dictionary of values to check

        Returns:
            List of Violation objects from OWL reasoning
        """
        violations = []

        loader = self._get_owl_loader()
        if loader is None or not loader.is_loaded:
            return violations

        try:
            from logic_guard_layer.ontology.loader import OWLViolation

            owl_violations = loader.validate_data(data)

            # Convert OWLViolation objects to Violation objects
            for owl_v in owl_violations:
                violation_type = self._map_owl_violation_type(owl_v.violation_type)
                violations.append(Violation(
                    type=violation_type,
                    constraint=owl_v.constraint_name,
                    message=owl_v.message,
                    property_name=owl_v.property_name,
                    actual_value=owl_v.actual_value,
                    expected_value=owl_v.expected_value,
                ))

        except Exception as e:
            logger.warning(f"OWL validation error: {e}")

        return violations

    def _map_owl_violation_type(self, owl_type: str) -> ViolationType:
        """Map OWL violation type string to ViolationType enum."""
        type_mapping = {
            "PHYSICAL_ERROR": ViolationType.PHYSICAL_ERROR,
            "RANGE_ERROR": ViolationType.RANGE_ERROR,
            "RELATIONAL_ERROR": ViolationType.RELATIONAL_ERROR,
            "TYPE_ERROR": ViolationType.TYPE_ERROR,
            "TEMPORAL_ERROR": ViolationType.TEMPORAL_ERROR,
        }
        return type_mapping.get(owl_type, ViolationType.UNKNOWN_ERROR)

    def _is_duplicate_violation(self, new_violation: Violation, existing_violations: list[Violation]) -> bool:
        """Check if a violation is a duplicate of an existing one.

        Helps avoid reporting the same issue from both OWL and rule-based checks.
        """
        for existing in existing_violations:
            # Check if same property and similar message
            if (new_violation.property_name == existing.property_name and
                new_violation.type == existing.type):
                return True
        return False

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

        Uses OWL type hierarchy if available for proper inheritance.

        Args:
            component_type: The component type name

        Returns:
            List of applicable constraints
        """
        # Try to get full type hierarchy from OWL
        loader = self._get_owl_loader()
        if loader is not None and loader.is_loaded:
            type_hierarchy = loader.get_type_hierarchy_for_validation(component_type)
        else:
            type_hierarchy = [component_type]

        # Find constraints that apply to any type in the hierarchy
        applicable = []
        for constraint in self.constraints:
            for type_name in type_hierarchy:
                if type_name in constraint.applicable_types:
                    applicable.append(constraint)
                    break
            # Also include constraints that apply to all components
            if "Component" in constraint.applicable_types or "Komponente" in constraint.applicable_types:
                if constraint not in applicable:
                    applicable.append(constraint)

        return applicable

    def validate_with_ontology(self, data: dict) -> ConsistencyResult:
        """
        Validate data using OWL reasoning combined with rule-based checking.

        This method explicitly uses OWL reasoning regardless of the
        use_owl_reasoning setting.

        Args:
            data: Dictionary of values to check

        Returns:
            ConsistencyResult
        """
        start_time = time.time()
        violations = []
        owl_violations_count = 0

        # Always try OWL validation in this method
        owl_violations = self._check_with_owl(data)
        owl_violations_count = len(owl_violations)
        violations.extend(owl_violations)

        # Also do rule-based checks
        result = self.check_consistency(data)

        # Merge violations (avoiding duplicates)
        for v in result.violations:
            if not self._is_duplicate_violation(v, violations):
                violations.append(v)

        processing_time = (time.time() - start_time) * 1000

        # Type validation using OWL
        loader = self._get_owl_loader()
        if loader is not None and loader.is_loaded:
            component_type = data.get("typ") or data.get("type")
            if component_type and not loader.is_valid_type(component_type):
                violations.append(
                    Violation(
                        type=ViolationType.TYPE_ERROR,
                        constraint="valid_type",
                        message=f"Unknown component type: {component_type}",
                        property_name="type",
                        actual_value=component_type,
                    )
                )

        return ConsistencyResult(
            is_consistent=len(violations) == 0,
            violations=violations,
            checked_constraints=len(self.constraints),
            processing_time_ms=processing_time,
            owl_violations_count=owl_violations_count,
        )

    def infer_component_type(self, data: dict) -> Optional[str]:
        """Infer the most specific component type based on data properties.

        Uses OWL ontology for type inference when available.

        Args:
            data: Dictionary with component properties

        Returns:
            Inferred type name or None
        """
        loader = self._get_owl_loader()
        if loader is not None and loader.is_loaded:
            return loader.infer_component_type(data)
        return None

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

    def get_owl_status(self) -> dict:
        """Get status information about OWL reasoning.

        Returns:
            Dictionary with OWL status info
        """
        loader = self._get_owl_loader()
        if loader is None:
            return {
                "enabled": self.use_owl_reasoning,
                "loaded": False,
                "concepts_count": 0,
                "properties_count": 0,
            }

        return {
            "enabled": self.use_owl_reasoning,
            "loaded": loader.is_loaded,
            "concepts_count": len(loader.get_concepts()) if loader.is_loaded else 0,
            "properties_count": len(loader.get_properties()) if loader.is_loaded else 0,
        }
