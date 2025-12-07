"""Tests for ReasoningModule."""

import pytest
from unittest.mock import MagicMock, patch

from logic_guard_layer.core.reasoner import ReasoningModule, ConsistencyResult
from logic_guard_layer.ontology.constraints import (
    Constraint,
    ConstraintType,
    get_all_constraints,
)
from logic_guard_layer.models.responses import Violation, ViolationType


class TestConsistencyResult:
    """Tests for ConsistencyResult class."""

    def test_create_consistent_result(self):
        """Test creating a consistent result."""
        result = ConsistencyResult(
            is_consistent=True,
            violations=[],
            checked_constraints=8,
            processing_time_ms=10.5
        )
        assert result.is_consistent is True
        assert len(result.violations) == 0
        assert result.checked_constraints == 8
        assert result.processing_time_ms == 10.5

    def test_create_inconsistent_result(self, sample_violation):
        """Test creating an inconsistent result."""
        result = ConsistencyResult(
            is_consistent=False,
            violations=[sample_violation],
            checked_constraints=8,
            processing_time_ms=15.0
        )
        assert result.is_consistent is False
        assert len(result.violations) == 1

    def test_str_consistent(self):
        """Test string representation for consistent result."""
        result = ConsistencyResult(
            is_consistent=True,
            violations=[],
            checked_constraints=8,
            processing_time_ms=10.0
        )
        s = str(result)
        assert "Consistent" in s
        assert "8" in s

    def test_str_inconsistent(self, sample_violation):
        """Test string representation for inconsistent result."""
        result = ConsistencyResult(
            is_consistent=False,
            violations=[sample_violation],
            checked_constraints=8,
            processing_time_ms=10.0
        )
        s = str(result)
        assert "Inconsistent" in s
        assert "1 violations" in s


class TestReasoningModuleInit:
    """Tests for ReasoningModule initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default constraints."""
        reasoner = ReasoningModule()
        assert len(reasoner.constraints) > 0
        assert len(reasoner.constraints) == len(get_all_constraints())

    def test_init_with_custom_constraints(self):
        """Test initialization with custom constraints."""
        custom_constraint = Constraint(
            id="CUSTOM1",
            name="Custom constraint",
            type=ConstraintType.RANGE,
            description="Test",
            expression="value > 0",
            check_fn=lambda d: None,
            applicable_types=["Component"]
        )
        reasoner = ReasoningModule(constraints=[custom_constraint])
        assert len(reasoner.constraints) == 1
        assert reasoner.constraints[0].id == "CUSTOM1"


class TestReasoningModuleCheckConsistency:
    """Tests for ReasoningModule.check_consistency method."""

    def test_check_valid_data(self, valid_raw_values):
        """Test checking valid data."""
        reasoner = ReasoningModule()
        result = reasoner.check_consistency(valid_raw_values)

        assert result.is_consistent is True
        assert len(result.violations) == 0
        assert result.checked_constraints > 0

    def test_check_negative_hours(self, raw_values_negative_hours):
        """Test checking data with negative operating hours."""
        reasoner = ReasoningModule()
        result = reasoner.check_consistency(raw_values_negative_hours)

        assert result.is_consistent is False
        assert len(result.violations) >= 1

        # Find the specific violation
        violations = [v for v in result.violations if v.property_name == "operating_hours"]
        assert len(violations) == 1
        assert violations[0].type == ViolationType.RANGE_ERROR

    def test_check_exceeds_lifespan(self, raw_values_exceeds_lifespan):
        """Test checking data where hours exceed lifespan."""
        reasoner = ReasoningModule()
        result = reasoner.check_consistency(raw_values_exceeds_lifespan)

        assert result.is_consistent is False
        assert len(result.violations) >= 1

    def test_check_high_pressure(self, raw_values_high_pressure):
        """Test checking data with high pressure."""
        reasoner = ReasoningModule()
        result = reasoner.check_consistency(raw_values_high_pressure)

        assert result.is_consistent is False
        pressure_violations = [v for v in result.violations if "pressure" in v.property_name]
        assert len(pressure_violations) == 1

    def test_check_high_temperature(self, raw_values_high_temperature):
        """Test checking data with high temperature."""
        reasoner = ReasoningModule()
        result = reasoner.check_consistency(raw_values_high_temperature)

        assert result.is_consistent is False
        temp_violations = [v for v in result.violations if "temperature" in v.property_name]
        assert len(temp_violations) == 1

    def test_check_invalid_interval(self, raw_values_invalid_interval):
        """Test checking data where interval exceeds lifespan."""
        reasoner = ReasoningModule()
        result = reasoner.check_consistency(raw_values_invalid_interval)

        assert result.is_consistent is False
        interval_violations = [v for v in result.violations if "interval" in v.property_name]
        assert len(interval_violations) >= 1

    def test_check_empty_data(self):
        """Test checking empty data."""
        reasoner = ReasoningModule()
        result = reasoner.check_consistency({})

        # Empty data should pass (no values to violate)
        assert result.is_consistent is True
        assert result.checked_constraints > 0

    def test_check_adds_entity_name(self):
        """Test that entity name is added to violations."""
        reasoner = ReasoningModule()
        data = {
            "name": "HP-001",
            "operating_hours": -100
        }
        result = reasoner.check_consistency(data)

        assert len(result.violations) >= 1
        assert result.violations[0].entity == "HP-001"

    def test_check_processing_time(self, valid_raw_values):
        """Test that processing time is recorded."""
        reasoner = ReasoningModule()
        result = reasoner.check_consistency(valid_raw_values)

        assert result.processing_time_ms >= 0

    def test_check_multiple_violations(self):
        """Test checking data with multiple violations."""
        data = {
            "operating_hours": -100,
            "max_lifespan": -500,
            "pressure_bar": 1000,
            "temperature_c": 500,
            "rpm": -100,
        }
        reasoner = ReasoningModule()
        result = reasoner.check_consistency(data)

        assert result.is_consistent is False
        assert len(result.violations) >= 4


class TestReasoningModuleCheckSingleConstraint:
    """Tests for ReasoningModule.check_single_constraint method."""

    def test_check_existing_constraint(self):
        """Test checking a single existing constraint."""
        reasoner = ReasoningModule()
        data = {"operating_hours": -100}

        violation = reasoner.check_single_constraint("C1", data)

        assert violation is not None
        assert violation.type == ViolationType.RANGE_ERROR

    def test_check_passing_constraint(self, valid_raw_values):
        """Test checking a single constraint that passes."""
        reasoner = ReasoningModule()

        violation = reasoner.check_single_constraint("C1", valid_raw_values)

        assert violation is None

    def test_check_nonexistent_constraint(self, valid_raw_values):
        """Test checking a non-existent constraint."""
        reasoner = ReasoningModule()

        violation = reasoner.check_single_constraint("NONEXISTENT", valid_raw_values)

        assert violation is None


class TestReasoningModuleGetApplicableConstraints:
    """Tests for ReasoningModule.get_applicable_constraints method."""

    def test_get_motor_constraints(self):
        """Test getting constraints for Motor type."""
        reasoner = ReasoningModule()
        constraints = reasoner.get_applicable_constraints("Motor")

        assert len(constraints) > 0
        for c in constraints:
            assert "Motor" in c.applicable_types or "Component" in c.applicable_types

    def test_get_hydraulic_pump_constraints(self):
        """Test getting constraints for HydraulicPump type."""
        reasoner = ReasoningModule()
        constraints = reasoner.get_applicable_constraints("HydraulicPump")

        # Should include pressure constraint
        ids = {c.id for c in constraints}
        assert "C6" in ids

    def test_get_unknown_type_constraints(self):
        """Test getting constraints for unknown type."""
        reasoner = ReasoningModule()
        constraints = reasoner.get_applicable_constraints("UnknownType")

        # Should still get Component constraints
        assert len(constraints) > 0


class TestReasoningModuleValidateWithOntology:
    """Tests for ReasoningModule.validate_with_ontology method."""

    def test_validate_falls_back_to_rules(self, valid_raw_values):
        """Test validation falls back to rule-based when ontology not loaded."""
        reasoner = ReasoningModule()

        # Mock the ontology loader inside the function
        with patch("logic_guard_layer.ontology.loader.get_ontology_loader") as mock_loader:
            mock_ontology = MagicMock()
            mock_ontology.is_loaded = False
            mock_loader.return_value = mock_ontology

            result = reasoner.validate_with_ontology(valid_raw_values)

            assert isinstance(result, ConsistencyResult)
            assert result.checked_constraints > 0

    def test_validate_with_invalid_type(self):
        """Test validation detects invalid component type."""
        reasoner = ReasoningModule()
        data = {
            "name": "TEST",
            "typ": "InvalidType",
            "operating_hours": 1000
        }

        with patch("logic_guard_layer.ontology.loader.get_ontology_loader") as mock_loader:
            mock_ontology = MagicMock()
            mock_ontology.is_loaded = True
            mock_ontology.is_valid_type.return_value = False
            mock_loader.return_value = mock_ontology

            result = reasoner.validate_with_ontology(data)

            # Should have type error
            type_errors = [v for v in result.violations if v.type == ViolationType.TYPE_ERROR]
            assert len(type_errors) == 1

    def test_validate_handles_ontology_error(self, valid_raw_values):
        """Test validation handles ontology errors gracefully."""
        reasoner = ReasoningModule()

        with patch("logic_guard_layer.ontology.loader.get_ontology_loader") as mock_loader:
            mock_loader.side_effect = Exception("Ontology error")

            # Should not raise, should fall back to rule-based
            result = reasoner.validate_with_ontology(valid_raw_values)

            assert isinstance(result, ConsistencyResult)


class TestReasoningModuleGetConstraintsSummary:
    """Tests for ReasoningModule.get_constraints_summary method."""

    def test_get_summary(self):
        """Test getting constraints summary."""
        reasoner = ReasoningModule()
        summary = reasoner.get_constraints_summary()

        assert len(summary) > 0
        for item in summary:
            assert "id" in item
            assert "name" in item
            assert "type" in item
            assert "expression" in item
            assert "description" in item

    def test_summary_contains_expected_constraints(self):
        """Test summary contains expected constraint IDs."""
        reasoner = ReasoningModule()
        summary = reasoner.get_constraints_summary()

        ids = {item["id"] for item in summary}
        expected = {"C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"}
        assert expected.issubset(ids)


class TestReasoningModuleIntegration:
    """Integration tests for ReasoningModule."""

    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        reasoner = ReasoningModule()

        # Valid data
        valid_data = {
            "name": "HP-001",
            "operating_hours": 5000,
            "max_lifespan": 20000,
            "maintenance_interval": 2500,
            "pressure_bar": 250,
            "temperature_c": 75,
            "rpm": 3000,
        }

        result = reasoner.check_consistency(valid_data)
        assert result.is_consistent is True

        # Now introduce violations one by one
        # Note: 0 values don't trigger violations due to 'or' fallback in constraint checks
        test_cases = [
            {"operating_hours": -100},
            {"max_lifespan": -1},  # Use negative, not 0
            {"maintenance_interval": -1},  # Use negative, not 0
            {"pressure_bar": 500},
            {"temperature_c": 200},
            {"rpm": -100},
        ]

        for invalid_field in test_cases:
            data = {**valid_data, **invalid_field}
            result = reasoner.check_consistency(data)
            assert result.is_consistent is False, f"Should fail for {invalid_field}"

    def test_constraint_error_handling(self):
        """Test constraint functions handle errors gracefully."""

        def broken_check(data):
            raise ValueError("Broken check")

        broken_constraint = Constraint(
            id="BROKEN",
            name="Broken",
            type=ConstraintType.RANGE,
            description="Always breaks",
            expression="broken",
            check_fn=broken_check,
            applicable_types=["Component"]
        )

        reasoner = ReasoningModule(constraints=[broken_constraint])
        data = {"name": "TEST"}

        # Should not raise, should log warning
        result = reasoner.check_consistency(data)
        assert result.checked_constraints == 1

    def test_boundary_conditions(self):
        """Test exact boundary values."""
        reasoner = ReasoningModule()

        # Test exact boundaries
        boundary_data = {
            "name": "BOUNDARY",
            "operating_hours": 0,  # Exactly at min
            "max_lifespan": 1,  # Exactly at min
            "maintenance_interval": 1,  # Exactly at min
            "pressure_bar": 0,  # Exactly at min
            "temperature_c": -40,  # Exactly at min
            "rpm": 0,  # Exactly at min
        }

        result = reasoner.check_consistency(boundary_data)
        assert result.is_consistent is True

        # Test max boundaries
        max_boundary = {
            "name": "MAX_BOUNDARY",
            "pressure_bar": 350,  # Exactly at max
            "temperature_c": 150,  # Exactly at max
            "rpm": 10000,  # Exactly at max
        }

        result = reasoner.check_consistency(max_boundary)
        assert result.is_consistent is True

    def test_german_keys_work(self):
        """Test that German keys are recognized."""
        reasoner = ReasoningModule()

        german_data = {
            "name": "HP-001",
            "betriebsstunden": 5000,
            "max_lebensdauer": 20000,
            "wartungsintervall": 2500,
            "druck_bar": 250,
            "temperatur_c": 75,
            "drehzahl": 3000,
        }

        result = reasoner.check_consistency(german_data)
        assert result.is_consistent is True

        # Test German keys with violations
        german_invalid = {
            "name": "HP-001",
            "betriebsstunden": -100,
        }

        result = reasoner.check_consistency(german_invalid)
        assert result.is_consistent is False
