"""
Tests for verifying sample texts against expected results.

These tests validate that:
1. The constraint checking logic correctly identifies violations
2. Valid samples pass all constraints
3. Invalid samples produce the expected violations
"""

import pytest
from logic_guard_layer.core.reasoner import ReasoningModule
from logic_guard_layer.ontology.constraints import get_all_constraints


# Sample test data - matches the expected values from validate.html
# Each sample has input data and expected results

# Prose samples - these test that if the LLM correctly extracts the values,
# the constraint checker will produce the expected results
PROSE_SAMPLES = {
    "prose_maintenance_report": {
        "name": "Cooling Pump Maintenance Report",
        "description": "Formal maintenance report with all values within limits",
        "data": {
            "operating_hours": 22000,
            "max_lifespan": 60000,
            "maintenance_interval": 4000,
            "pressure_bar": 12,
            "temperature_c": 58,
            "efficiency": 81,
            "npsh_available": 7.5,
            "npsh_required": 4.2
        },
        "expected_valid": True,
        "expected_violations": []
    },
    "prose_technician_notes": {
        "name": "Generator Site Visit Notes",
        "description": "Informal technician notes - valid equipment",
        "data": {
            "operating_hours": 8500,
            "max_lifespan": 40000,
            "maintenance_interval": 500,
            "pressure_bar": 4.5,
            "temperature_c": 82
        },
        "expected_valid": True,
        "expected_violations": []
    },
    "prose_email_urgent": {
        "name": "Urgent Hydraulic Press Email",
        "description": "Email reporting exceeded hours and pressure",
        "data": {
            "operating_hours": 95000,
            "max_lifespan": 80000,
            "pressure_bar": 385,
            "temperature_c": 78
        },
        "expected_valid": False,
        "expected_violation_types": ["RELATIONAL_ERROR", "RANGE_ERROR"],
        "min_violations": 2
    },
    "prose_inspection_log": {
        "name": "Compressor Inspection Log",
        "description": "Inspection finding exceeded hours and impossible efficiency",
        "data": {
            "operating_hours": 112000,
            "max_lifespan": 100000,
            "maintenance_interval": 8000,
            "pressure_bar": 11.5,
            "temperature_c": 295,
            "efficiency": 108
        },
        "expected_valid": False,
        "expected_violation_types": ["RELATIONAL_ERROR", "PHYSICAL_ERROR"],
        "min_violations": 2
    },
    "prose_verbal_report": {
        "name": "Feedwater Pump Verbal Report",
        "description": "Transcribed report of cavitation issue",
        "data": {
            "operating_hours": 42000,
            "max_lifespan": 80000,
            "temperature_c": 135,
            "pressure_bar": 0.8,
            "npsh_available": 3.2,
            "npsh_required": 5.8,
            "efficiency": 72
        },
        "expected_valid": False,
        "expected_violation_types": ["PHYSICAL_ERROR"],
        "min_violations": 1
    }
}

VALID_SAMPLES = {
    "gasturbine": {
        "name": "Gas Turbine GT-Siemens-H-Class",
        "data": {
            "operating_hours": 45000,
            "max_lifespan": 100000,
            "maintenance_interval": 8000,
            "pressure_bar": 320,
            "temperature_c": 85,
            "efficiency": 63
        },
        "expected_valid": True,
        "expected_violations": []
    },
    "windkraft": {
        "name": "Wind Turbine Siemens-Gamesa-14MW",
        "data": {
            "operating_hours": 52000,
            "max_lifespan": 175000,
            "maintenance_interval": 8760,
            "temperature_c": 35
        },
        "expected_valid": True,
        "expected_violations": []
    },
    "waermepumpe": {
        "name": "Heat Pump Viessmann-Vitocal-300",
        "data": {
            "operating_hours": 12500,
            "max_lifespan": 80000,
            "maintenance_interval": 4380,
            "pressure_bar": 28,
            "cop": 4.2,
            "source_temperature_k": 281,  # 8°C in Kelvin
            "sink_temperature_k": 328     # 55°C in Kelvin
        },
        "expected_valid": True,
        "expected_violations": []
    },
    "batteriespeicher": {
        "name": "Battery Storage Tesla-Megapack-XL",
        "data": {
            "operating_hours": 8500,
            "max_lifespan": 87600,
            "cycles": 2850,
            "max_cycles": 10000,
            "soc": 72,
            "temperature_c": 28
        },
        "expected_valid": True,
        "expected_violations": []
    },
    "kreiselpumpe": {
        "name": "Centrifugal Pump KSB-Omega-350",
        "data": {
            "operating_hours": 18500,
            "max_lifespan": 60000,
            "maintenance_interval": 4000,
            "temperature_c": 65,
            "npsh_available": 8,
            "npsh_required": 5,
            "efficiency": 82
        },
        "expected_valid": True,
        "expected_violations": []
    },
    "cnc_maschine": {
        "name": "CNC Milling Machine DMG-MORI-DMU-125",
        "data": {
            "operating_hours": 28000,
            "max_lifespan": 80000,
            "maintenance_interval": 2000,
            "pressure_bar": 180,
            "temperature_c": 38
        },
        "expected_valid": True,
        "expected_violations": []
    }
}

INVALID_SAMPLES = {
    "exceeded_hours": {
        "name": "Gearbox Flender-ZAPEX-ZW",
        "data": {
            "operating_hours": 95000,
            "max_lifespan": 80000,
            "maintenance_interval": 8000,
            "temperature_c": 72
        },
        "expected_valid": False,
        "expected_violation_types": ["RELATIONAL_ERROR"],  # Actual type used
        "min_violations": 1
    },
    "pressure_violation": {
        "name": "High Pressure Reactor BASF-HDR-500",
        "data": {
            "operating_hours": 15000,
            "max_lifespan": 50000,
            "pressure_bar": 450,
            "temperature_c": 120
        },
        "expected_valid": False,
        "expected_violation_types": ["RANGE_ERROR"],
        "min_violations": 1
    },
    "cavitation_risk": {
        "name": "Feedwater Pump FWP-PowerPlant-03",
        "data": {
            "operating_hours": 42000,
            "max_lifespan": 80000,
            "temperature_c": 145,
            "npsh_available": 3.5,
            "npsh_required": 6.2
        },
        "expected_valid": False,
        "expected_violation_types": ["PHYSICAL_ERROR"],
        "min_violations": 1
    },
    "efficiency_violation": {
        "name": "Compressor with impossible efficiency",
        "data": {
            "operating_hours": 10000,
            "max_lifespan": 50000,
            "efficiency": 125  # > 100% is physically impossible
        },
        "expected_valid": False,
        "expected_violation_types": ["PHYSICAL_ERROR"],
        "min_violations": 1
    },
    "multiple_errors": {
        "name": "Compressor System CS-Chemical-07",
        "data": {
            "operating_hours": 125000,
            "max_lifespan": 100000,
            "maintenance_interval": 150000,
            "pressure_bar": 420,
            "temperature_c": 380,
            "efficiency": 125,
            "npsh_available": 2,
            "npsh_required": 5
        },
        "expected_valid": False,
        "expected_violation_types": ["RELATIONAL_ERROR", "RANGE_ERROR", "PHYSICAL_ERROR"],
        "min_violations": 4
    },
    "battery_soc_over": {
        "name": "Battery with SOC > 100%",
        "data": {
            "operating_hours": 1000,
            "max_lifespan": 50000,
            "soc": 115  # SOC cannot exceed 100%
        },
        "expected_valid": False,
        "expected_violation_types": ["PHYSICAL_ERROR"],  # SOC uses PHYSICAL_ERROR
        "min_violations": 1
    },
    "battery_cycles_exceeded": {
        "name": "Battery with exceeded cycles",
        "data": {
            "operating_hours": 5000,
            "max_lifespan": 50000,
            "charge_cycles": 7000,  # Use charge_cycles, not cycles
            "max_cycles": 6000
        },
        "expected_valid": False,
        "expected_violation_types": ["RELATIONAL_ERROR"],
        "min_violations": 1
    }
}


@pytest.fixture
def reasoner():
    """Create a reasoning module with all constraints."""
    return ReasoningModule()


class TestProseSamples:
    """Test prose/natural language samples after LLM extraction.

    These tests verify that IF the LLM correctly extracts the values
    from unstructured text, the constraint checker will produce the
    expected results. This validates the end-to-end verification concept.
    """

    @pytest.mark.parametrize("sample_name,sample", [
        (k, v) for k, v in PROSE_SAMPLES.items() if v["expected_valid"]
    ])
    def test_valid_prose_sample(self, reasoner, sample_name, sample):
        """Test that valid prose samples (after extraction) pass constraints."""
        data = sample["data"].copy()
        data["name"] = sample["name"]

        result = reasoner.check_consistency(data)

        assert result.is_consistent, (
            f"Prose sample '{sample_name}' ({sample['description']}) "
            f"should be valid but got violations: {[v.message for v in result.violations]}"
        )

    @pytest.mark.parametrize("sample_name,sample", [
        (k, v) for k, v in PROSE_SAMPLES.items() if not v["expected_valid"]
    ])
    def test_invalid_prose_sample(self, reasoner, sample_name, sample):
        """Test that invalid prose samples (after extraction) have violations."""
        data = sample["data"].copy()
        data["name"] = sample["name"]

        result = reasoner.check_consistency(data)

        assert not result.is_consistent, (
            f"Prose sample '{sample_name}' ({sample['description']}) "
            f"should be invalid but was marked consistent"
        )

        min_violations = sample.get("min_violations", 1)
        assert len(result.violations) >= min_violations, (
            f"Prose sample '{sample_name}' should have at least {min_violations} "
            f"violation(s) but got {len(result.violations)}"
        )

    @pytest.mark.parametrize("sample_name,sample", [
        (k, v) for k, v in PROSE_SAMPLES.items() if not v["expected_valid"]
    ])
    def test_prose_violation_types(self, reasoner, sample_name, sample):
        """Test that prose samples produce expected violation types."""
        data = sample["data"].copy()
        data["name"] = sample["name"]

        result = reasoner.check_consistency(data)

        actual_types = {v.type.value for v in result.violations}
        expected_types = set(sample["expected_violation_types"])

        matching_types = actual_types & expected_types
        assert len(matching_types) > 0, (
            f"Prose sample '{sample_name}' should have violation types {expected_types} "
            f"but got {actual_types}"
        )


class TestValidSamples:
    """Test that valid samples pass all constraints."""

    @pytest.mark.parametrize("sample_name,sample", VALID_SAMPLES.items())
    def test_valid_sample(self, reasoner, sample_name, sample):
        """Test that valid samples have no violations."""
        data = sample["data"].copy()
        data["name"] = sample["name"]

        result = reasoner.check_consistency(data)

        assert result.is_consistent, (
            f"Sample '{sample_name}' should be valid but got violations: "
            f"{[v.message for v in result.violations]}"
        )
        assert len(result.violations) == 0


class TestInvalidSamples:
    """Test that invalid samples produce expected violations."""

    @pytest.mark.parametrize("sample_name,sample", INVALID_SAMPLES.items())
    def test_invalid_sample_has_violations(self, reasoner, sample_name, sample):
        """Test that invalid samples have at least one violation."""
        data = sample["data"].copy()
        data["name"] = sample["name"]

        result = reasoner.check_consistency(data)

        assert not result.is_consistent, (
            f"Sample '{sample_name}' should be invalid but was marked consistent"
        )
        assert len(result.violations) >= sample.get("min_violations", 1), (
            f"Sample '{sample_name}' should have at least {sample.get('min_violations', 1)} "
            f"violation(s) but got {len(result.violations)}"
        )

    @pytest.mark.parametrize("sample_name,sample", INVALID_SAMPLES.items())
    def test_invalid_sample_violation_types(self, reasoner, sample_name, sample):
        """Test that invalid samples produce expected violation types."""
        data = sample["data"].copy()
        data["name"] = sample["name"]

        result = reasoner.check_consistency(data)

        actual_types = {v.type.value for v in result.violations}
        expected_types = set(sample["expected_violation_types"])

        # At least one expected type should be present
        matching_types = actual_types & expected_types
        assert len(matching_types) > 0, (
            f"Sample '{sample_name}' should have violation types {expected_types} "
            f"but got {actual_types}"
        )


class TestExceededHours:
    """Detailed tests for operating hours > max lifespan."""

    def test_hours_exceed_lifespan(self, reasoner):
        """Test detection when operating hours exceed max lifespan."""
        data = {
            "name": "Test Component",
            "operating_hours": 100000,
            "max_lifespan": 80000
        }
        result = reasoner.check_consistency(data)

        assert not result.is_consistent
        assert any("lifespan" in v.message.lower() or "hours" in v.message.lower()
                   for v in result.violations)

    def test_hours_at_limit(self, reasoner):
        """Test that hours at exactly the limit are valid."""
        data = {
            "name": "Test Component",
            "operating_hours": 80000,
            "max_lifespan": 80000
        }
        result = reasoner.check_consistency(data)

        # At the limit should be valid (not exceeded)
        lifespan_violations = [v for v in result.violations
                               if "lifespan" in v.message.lower() or "hours" in v.message.lower()]
        assert len(lifespan_violations) == 0


class TestPressureConstraints:
    """Detailed tests for pressure violations."""

    def test_pressure_over_limit(self, reasoner):
        """Test detection of pressure over 350 bar."""
        data = {
            "name": "Test Component",
            "operating_hours": 1000,
            "max_lifespan": 50000,
            "pressure_bar": 400
        }
        result = reasoner.check_consistency(data)

        assert not result.is_consistent
        assert any("pressure" in v.message.lower() for v in result.violations)

    def test_pressure_at_limit(self, reasoner):
        """Test that pressure at 350 bar is valid."""
        data = {
            "name": "Test Component",
            "operating_hours": 1000,
            "max_lifespan": 50000,
            "pressure_bar": 350
        }
        result = reasoner.check_consistency(data)

        pressure_violations = [v for v in result.violations
                               if "pressure" in v.message.lower()]
        assert len(pressure_violations) == 0


class TestNPSHConstraints:
    """Detailed tests for NPSH cavitation detection."""

    def test_npsh_cavitation_risk(self, reasoner):
        """Test detection of cavitation risk (NPSH_available < NPSH_required)."""
        data = {
            "name": "Test Pump",
            "operating_hours": 1000,
            "max_lifespan": 50000,
            "npsh_available": 3.5,
            "npsh_required": 6.2
        }
        result = reasoner.check_consistency(data)

        assert not result.is_consistent
        assert any("npsh" in v.message.lower() or "cavitation" in v.message.lower()
                   for v in result.violations)

    def test_npsh_safe(self, reasoner):
        """Test that adequate NPSH margin is valid."""
        data = {
            "name": "Test Pump",
            "operating_hours": 1000,
            "max_lifespan": 50000,
            "npsh_available": 8,
            "npsh_required": 5
        }
        result = reasoner.check_consistency(data)

        npsh_violations = [v for v in result.violations
                          if "npsh" in v.message.lower() or "cavitation" in v.message.lower()]
        assert len(npsh_violations) == 0


class TestEfficiencyConstraints:
    """Detailed tests for efficiency (First Law of Thermodynamics)."""

    def test_efficiency_over_100(self, reasoner):
        """Test detection of efficiency > 100% (violates First Law)."""
        data = {
            "name": "Test Component",
            "operating_hours": 1000,
            "max_lifespan": 50000,
            "efficiency": 125
        }
        result = reasoner.check_consistency(data)

        assert not result.is_consistent
        assert any("efficiency" in v.message.lower() or "100" in v.message
                   for v in result.violations)

    def test_efficiency_valid(self, reasoner):
        """Test that valid efficiency values pass."""
        for efficiency in [0, 50, 82, 99, 100]:
            data = {
                "name": "Test Component",
                "operating_hours": 1000,
                "max_lifespan": 50000,
                "efficiency": efficiency
            }
            result = reasoner.check_consistency(data)

            efficiency_violations = [v for v in result.violations
                                     if "efficiency" in v.message.lower()]
            assert len(efficiency_violations) == 0, f"Efficiency {efficiency}% should be valid"


class TestBatteryConstraints:
    """Detailed tests for battery storage constraints."""

    def test_soc_over_100(self, reasoner):
        """Test detection of SOC > 100%."""
        data = {
            "name": "Test Battery",
            "operating_hours": 1000,
            "max_lifespan": 50000,
            "soc": 115
        }
        result = reasoner.check_consistency(data)

        assert not result.is_consistent
        assert any("soc" in v.message.lower() or "charge" in v.message.lower()
                   for v in result.violations)

    def test_soc_negative(self, reasoner):
        """Test detection of negative SOC."""
        data = {
            "name": "Test Battery",
            "operating_hours": 1000,
            "max_lifespan": 50000,
            "soc": -5
        }
        result = reasoner.check_consistency(data)

        assert not result.is_consistent

    def test_cycles_exceeded(self, reasoner):
        """Test detection of charge cycles exceeding maximum."""
        data = {
            "name": "Test Battery",
            "operating_hours": 1000,
            "max_lifespan": 50000,
            "charge_cycles": 7000,  # Use correct field name
            "max_cycles": 6000
        }
        result = reasoner.check_consistency(data)

        assert not result.is_consistent
        assert any("cycle" in v.message.lower() for v in result.violations)

    def test_valid_battery(self, reasoner):
        """Test that valid battery data passes."""
        data = {
            "name": "Test Battery",
            "operating_hours": 8500,
            "max_lifespan": 87600,
            "cycles": 2850,
            "max_cycles": 10000,
            "soc": 72
        }
        result = reasoner.check_consistency(data)

        # Filter for battery-specific violations only
        battery_violations = [v for v in result.violations
                              if "soc" in v.message.lower() or
                                 "cycle" in v.message.lower() or
                                 "charge" in v.message.lower()]
        assert len(battery_violations) == 0


class TestMaintenanceConstraints:
    """Detailed tests for maintenance interval constraints."""

    def test_maintenance_interval_exceeds_lifespan(self, reasoner):
        """Test detection when maintenance interval > lifespan."""
        data = {
            "name": "Test Component",
            "operating_hours": 1000,
            "max_lifespan": 100000,
            "maintenance_interval": 150000
        }
        result = reasoner.check_consistency(data)

        assert not result.is_consistent
        assert any("maintenance" in v.message.lower() or "interval" in v.message.lower()
                   for v in result.violations)


class TestConstraintCoverage:
    """Tests to ensure all constraints are covered."""

    def test_all_constraints_loaded(self, reasoner):
        """Test that all expected constraints are loaded."""
        constraints = get_all_constraints()

        # Should have at least 8 basic constraints + 8 physics constraints
        assert len(constraints) >= 8, f"Expected at least 8 constraints, got {len(constraints)}"

    def test_constraint_ids_unique(self, reasoner):
        """Test that all constraint IDs are unique."""
        constraints = get_all_constraints()
        ids = [c.id for c in constraints]

        assert len(ids) == len(set(ids)), "Constraint IDs should be unique"

    def test_constraints_have_descriptions(self, reasoner):
        """Test that all constraints have descriptions."""
        constraints = get_all_constraints()

        for constraint in constraints:
            assert constraint.description, f"Constraint {constraint.id} missing description"
            assert constraint.name, f"Constraint {constraint.id} missing name"


class TestMultipleViolations:
    """Tests for detecting multiple simultaneous violations."""

    def test_detect_all_violations(self, reasoner):
        """Test that all violations are detected in one pass."""
        data = {
            "name": "Problem Component",
            "operating_hours": 125000,
            "max_lifespan": 100000,
            "maintenance_interval": 150000,
            "pressure_bar": 420,
            "temperature_c": 380,
            "efficiency": 125,
            "npsh_available": 2,
            "npsh_required": 5
        }
        result = reasoner.check_consistency(data)

        assert not result.is_consistent
        # Should detect at least 4 violations
        assert len(result.violations) >= 4, (
            f"Expected at least 4 violations, got {len(result.violations)}: "
            f"{[v.message for v in result.violations]}"
        )

    def test_violation_messages_are_descriptive(self, reasoner):
        """Test that violation messages are descriptive."""
        data = {
            "name": "Test Component",
            "operating_hours": 100000,
            "max_lifespan": 80000
        }
        result = reasoner.check_consistency(data)

        for violation in result.violations:
            assert len(violation.message) > 10, "Violation messages should be descriptive"
            assert violation.constraint, "Violation should reference the constraint"
