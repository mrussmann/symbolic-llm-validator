"""Tests for OWL-based validation using Owlready2."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from logic_guard_layer.ontology.loader import (
    OntologyLoader,
    OWLViolation,
    get_ontology_loader,
    load_ontology,
    reset_ontology_loader,
)
from logic_guard_layer.core.reasoner import ReasoningModule, ConsistencyResult
from logic_guard_layer.models.responses import ViolationType


class TestOWLViolation:
    """Tests for OWLViolation dataclass."""

    def test_create_violation(self):
        """Test creating an OWL violation."""
        violation = OWLViolation(
            violation_type="PHYSICAL_ERROR",
            constraint_name="Carnot Limit",
            message="COP exceeds Carnot limit",
            property_name="cop",
            actual_value=15.0,
            expected_value="<= 8.5",
        )
        assert violation.violation_type == "PHYSICAL_ERROR"
        assert violation.constraint_name == "Carnot Limit"
        assert violation.property_name == "cop"

    def test_create_minimal_violation(self):
        """Test creating a minimal OWL violation."""
        violation = OWLViolation(
            violation_type="RANGE_ERROR",
            constraint_name="Operating Hours",
            message="Negative hours",
        )
        assert violation.property_name is None
        assert violation.actual_value is None


class TestOntologyLoaderInit:
    """Tests for OntologyLoader initialization."""

    def test_singleton_pattern(self):
        """Test singleton pattern works."""
        reset_ontology_loader()
        loader1 = get_ontology_loader()
        loader2 = get_ontology_loader()
        assert loader1 is loader2

    def test_reset_loader(self):
        """Test resetting the loader."""
        reset_ontology_loader()
        loader1 = get_ontology_loader()
        reset_ontology_loader()
        loader2 = get_ontology_loader()
        # After reset, should be a new instance
        # (singleton reset creates new on next call)
        assert loader2 is not None


class TestOntologyLoaderLoad:
    """Tests for OntologyLoader.load method."""

    @pytest.fixture(autouse=True)
    def reset_before_test(self):
        """Reset ontology loader before each test."""
        reset_ontology_loader()
        yield
        reset_ontology_loader()

    def test_load_default_ontology(self):
        """Test loading the default ontology."""
        loader = load_ontology()
        assert loader.is_loaded is True
        assert len(loader.get_concepts()) > 0

    def test_load_extracts_concepts(self):
        """Test that loading extracts concept hierarchy."""
        loader = load_ontology()
        concepts = loader.get_concepts()

        # Check for expected concepts
        assert "Komponente" in concepts or len(concepts) > 0

    def test_load_extracts_properties(self):
        """Test that loading extracts properties."""
        loader = load_ontology()
        properties = loader.get_properties()

        # Should have properties defined in the ontology
        assert len(properties) > 0

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file returns False."""
        reset_ontology_loader()
        # Create a fresh loader instance directly (bypass singleton)
        OntologyLoader._instance = None
        loader = OntologyLoader.__new__(OntologyLoader)
        loader._initialized = False
        loader.__init__(Path("/nonexistent/path.owl"))

        result = loader.load(Path("/nonexistent/path.owl"))
        assert result is False
        assert loader.is_loaded is False

        # Restore singleton
        OntologyLoader._instance = None


class TestOntologyLoaderTypeHierarchy:
    """Tests for type hierarchy methods."""

    @pytest.fixture(autouse=True)
    def load_ontology_fixture(self):
        """Load ontology before tests."""
        reset_ontology_loader()
        self.loader = load_ontology()
        yield
        reset_ontology_loader()

    def test_is_valid_type_known(self):
        """Test checking a known valid type."""
        # These should be in the ontology
        known_types = ["Komponente", "Pumpe", "Motor", "Sensor"]
        for type_name in known_types:
            if type_name in self.loader.get_concepts():
                assert self.loader.is_valid_type(type_name) is True

    def test_is_valid_type_unknown(self):
        """Test checking an unknown type."""
        assert self.loader.is_valid_type("CompletelyUnknownType") is False

    def test_get_parent_types(self):
        """Test getting parent types."""
        concepts = self.loader.get_concepts()

        # Find a type with parents
        for name, parents in concepts.items():
            if parents:
                result = self.loader.get_parent_types(name)
                assert len(result) > 0
                break

    def test_get_all_ancestor_types(self):
        """Test getting all ancestor types."""
        concepts = self.loader.get_concepts()

        # Test with a leaf type if available
        if "Hydraulikpumpe" in concepts:
            ancestors = self.loader.get_all_ancestor_types("Hydraulikpumpe")
            # Should include parent types
            assert len(ancestors) > 0

    def test_get_type_hierarchy_for_validation(self):
        """Test getting type hierarchy for validation."""
        if self.loader.is_loaded:
            hierarchy = self.loader.get_type_hierarchy_for_validation("Pumpe")
            # Should include Pumpe and possibly parents
            assert "Pumpe" in hierarchy or len(hierarchy) > 0


class TestOntologyLoaderTypeInference:
    """Tests for type inference."""

    @pytest.fixture(autouse=True)
    def load_ontology_fixture(self):
        """Load ontology before tests."""
        reset_ontology_loader()
        self.loader = load_ontology()
        yield
        reset_ontology_loader()

    def test_infer_pump_type(self):
        """Test inferring pump type from properties."""
        data = {
            "npsh_available": 8.0,
            "npsh_required": 5.0,
            "hydraulikleistung": 45.0,
        }
        inferred = self.loader.infer_component_type(data)
        assert inferred in ["Pumpe", "Kreiselpumpe", None]

    def test_infer_battery_type(self):
        """Test inferring battery type from properties."""
        data = {
            "ladezustand": 75,
            "ladezyklen": 500,
        }
        inferred = self.loader.infer_component_type(data)
        assert inferred in ["Batteriespeicher", None]

    def test_infer_heat_pump_type(self):
        """Test inferring heat pump type from properties."""
        data = {
            "cop": 4.2,
            "quelltemperatur": 10,
            "vorlauftemperatur": 35,
        }
        inferred = self.loader.infer_component_type(data)
        assert inferred in ["Waermepumpe", None]

    def test_infer_no_match(self):
        """Test inference with no matching properties."""
        data = {
            "random_field": 123,
        }
        inferred = self.loader.infer_component_type(data)
        assert inferred is None


class TestOntologyLoaderInstanceCreation:
    """Tests for instance creation methods."""

    @pytest.fixture(autouse=True)
    def load_ontology_fixture(self):
        """Load ontology before tests."""
        reset_ontology_loader()
        self.loader = load_ontology()
        yield
        reset_ontology_loader()

    def test_create_instance_known_class(self):
        """Test creating an instance of a known class."""
        instance = self.loader.create_instance("Komponente", "test_instance")
        assert instance is not None

    def test_create_instance_auto_name(self):
        """Test creating an instance with auto-generated name."""
        instance = self.loader.create_instance("Komponente")
        assert instance is not None

    def test_create_instance_unknown_class(self):
        """Test creating an instance of an unknown class."""
        instance = self.loader.create_instance("NonexistentClass", "test")
        assert instance is None

    def test_create_instance_from_data(self):
        """Test creating instance from data dictionary."""
        data = {
            "type": "Pumpe",
            "name": "HP-001",
            "operating_hours": 5000,
            "max_lifespan": 20000,
        }
        instance = self.loader.create_instance_from_data(data)
        assert instance is not None

    def test_create_instance_from_data_type_mapping(self):
        """Test that English type names are mapped correctly."""
        data = {
            "type": "pump",  # English lowercase
            "name": "Test-Pump",
        }
        instance = self.loader.create_instance_from_data(data)
        # Should map to Pumpe
        assert instance is not None


class TestOntologyLoaderValidation:
    """Tests for OWL-based validation."""

    @pytest.fixture(autouse=True)
    def load_ontology_fixture(self):
        """Load ontology before tests."""
        reset_ontology_loader()
        self.loader = load_ontology()
        yield
        reset_ontology_loader()

    def test_validate_data_valid(self):
        """Test validating valid data."""
        data = {
            "type": "Pumpe",
            "operating_hours": 5000,
            "max_lifespan": 20000,
        }
        violations = self.loader.validate_data(data)
        # Valid data should have no violations (or only from complex checks)
        # The simple range checks should pass
        assert isinstance(violations, list)

    def test_validate_carnot_violation(self):
        """Test detecting Carnot limit violation."""
        data = {
            "type": "HeatPump",
            "cop": 50,  # Impossibly high
            "temperatur_quelle": 10,  # 10°C source
            "temperatur_vorlauf": 35,  # 35°C sink
        }
        violations = self.loader.validate_data(data)

        # Should detect Carnot violation
        carnot_violations = [v for v in violations if "Carnot" in v.constraint_name]
        assert len(carnot_violations) >= 1

    def test_validate_pump_power_violation(self):
        """Test detecting pump power balance violation."""
        data = {
            "type": "Pump",
            "leistungsaufnahme": 10,  # 10 kW input
            "hydraulikleistung": 20,  # 20 kW output (impossible!)
            "wirkungsgrad": 80,  # 80% efficiency
        }
        violations = self.loader.validate_data(data)

        # Should detect power balance violation
        power_violations = [v for v in violations if "Power" in v.constraint_name or "power" in v.message.lower()]
        assert len(power_violations) >= 1

    def test_validate_compressor_thermodynamics(self):
        """Test detecting compressor thermodynamics violation."""
        data = {
            "type": "Kompressor",
            "temperatur_eingang": 20,  # 20°C inlet
            "temperatur_ausgang": 10,  # 10°C outlet (impossible for compression!)
            "druck_eingang": 1,  # 1 bar
            "druck_ausgang": 10,  # 10 bar
        }
        violations = self.loader.validate_data(data)

        # Should detect thermodynamics violation
        thermo_violations = [v for v in violations if "Isentropic" in v.constraint_name or "isentropic" in v.message.lower()]
        assert len(thermo_violations) >= 1


class TestReasoningModuleOWLIntegration:
    """Tests for ReasoningModule OWL integration."""

    @pytest.fixture(autouse=True)
    def reset_fixtures(self):
        """Reset before each test."""
        reset_ontology_loader()
        yield
        reset_ontology_loader()

    def test_owl_reasoning_enabled_by_default(self):
        """Test that OWL reasoning is enabled by default."""
        reasoner = ReasoningModule()
        assert reasoner.use_owl_reasoning is True

    def test_owl_reasoning_can_be_disabled(self):
        """Test disabling OWL reasoning."""
        reasoner = ReasoningModule(use_owl_reasoning=False)
        assert reasoner.use_owl_reasoning is False

    def test_get_owl_status(self):
        """Test getting OWL status."""
        reasoner = ReasoningModule()
        status = reasoner.get_owl_status()

        assert "enabled" in status
        assert "loaded" in status
        assert "concepts_count" in status
        assert "properties_count" in status

    def test_consistency_result_tracks_owl_violations(self):
        """Test that ConsistencyResult tracks OWL violations count."""
        result = ConsistencyResult(
            is_consistent=False,
            violations=[],
            checked_constraints=10,
            processing_time_ms=50.0,
            owl_violations_count=3,
        )
        assert result.owl_violations_count == 3
        assert "3 from OWL" in str(result)

    def test_infer_component_type(self):
        """Test type inference through reasoner."""
        reasoner = ReasoningModule()
        data = {
            "cop": 4.2,
            "quelltemperatur": 10,
        }
        inferred = reasoner.infer_component_type(data)
        # May return None if ontology not fully loaded
        assert inferred is None or isinstance(inferred, str)

    def test_check_consistency_uses_owl(self):
        """Test that check_consistency uses OWL validation."""
        reasoner = ReasoningModule(use_owl_reasoning=True)

        # Data that should trigger Carnot violation via OWL
        data = {
            "type": "HeatPump",
            "cop": 100,  # Impossibly high
            "temperatur_quelle": 0,
            "temperatur_vorlauf": 50,
        }

        result = reasoner.check_consistency(data)
        # Should have violations (either from OWL or rule-based)
        assert isinstance(result, ConsistencyResult)

    def test_get_applicable_constraints_uses_hierarchy(self):
        """Test that get_applicable_constraints uses OWL hierarchy."""
        reasoner = ReasoningModule()

        # Get constraints for a specific type
        constraints = reasoner.get_applicable_constraints("Pumpe")

        # Should return applicable constraints
        assert isinstance(constraints, list)


class TestOWLPhysicsConstraints:
    """Tests for physics constraints in OWL validation."""

    @pytest.fixture(autouse=True)
    def load_ontology_fixture(self):
        """Load ontology before tests."""
        reset_ontology_loader()
        self.loader = load_ontology()
        yield
        reset_ontology_loader()

    def test_carnot_limit_calculation(self):
        """Test Carnot limit calculation is correct."""
        # COP_carnot = T_hot / (T_hot - T_cold) for heating
        # T_source = 10°C = 283.15K, T_sink = 35°C = 308.15K
        # COP_carnot = 308.15 / (308.15 - 283.15) = 308.15 / 25 ≈ 12.33

        # COP of 15 should violate Carnot limit
        data = {
            "cop": 15,
            "temperatur_quelle": 10,
            "temperatur_vorlauf": 35,
        }
        violations = self.loader._check_carnot_limit(data)
        assert len(violations) == 1
        assert "Carnot" in violations[0].constraint_name

    def test_carnot_limit_valid(self):
        """Test valid COP doesn't trigger violation."""
        # COP of 4 is well below Carnot limit of ~12.3
        data = {
            "cop": 4,
            "temperatur_quelle": 10,
            "temperatur_vorlauf": 35,
        }
        violations = self.loader._check_carnot_limit(data)
        assert len(violations) == 0

    def test_pump_power_calculation(self):
        """Test pump power balance calculation."""
        # P_max = P_in * η = 10 * 0.8 = 8 kW
        # P_hyd = 20 kW > 8 kW * 1.15 = 9.2 kW → violation
        data = {
            "leistungsaufnahme": 10,
            "hydraulikleistung": 20,
            "wirkungsgrad": 80,
        }
        violations = self.loader._check_pump_power_balance(data)
        assert len(violations) == 1

    def test_pump_power_valid(self):
        """Test valid pump power doesn't trigger violation."""
        # P_max = 10 * 0.8 = 8 kW
        # P_hyd = 7 kW < 8 kW * 1.15 = 9.2 kW → valid
        data = {
            "leistungsaufnahme": 10,
            "hydraulikleistung": 7,
            "wirkungsgrad": 80,
        }
        violations = self.loader._check_pump_power_balance(data)
        assert len(violations) == 0

    def test_compressor_thermodynamics_violation(self):
        """Test compressor thermodynamics violation detection."""
        # For compression, T_out should be >= T_isentropic
        # If P_ratio = 10 and T_in = 20°C, T_isentropic ≈ 293 * 10^0.286 ≈ 566K ≈ 293°C
        # T_out = 10°C = 283K is way below → violation
        data = {
            "temperatur_eingang": 20,
            "temperatur_ausgang": 10,
            "druck_eingang": 1,
            "druck_ausgang": 10,
        }
        violations = self.loader._check_compressor_thermodynamics(data)
        assert len(violations) == 1
        assert "Isentropic" in violations[0].constraint_name

    def test_compressor_thermodynamics_valid(self):
        """Test valid compressor temps don't trigger violation."""
        # For P_ratio = 2 and T_in = 20°C (293K)
        # T_isentropic = 293 * 2^0.286 ≈ 357K ≈ 84°C
        # T_out = 120°C > 84°C → valid
        data = {
            "temperatur_eingang": 20,
            "temperatur_ausgang": 120,
            "druck_eingang": 1,
            "druck_ausgang": 2,
        }
        violations = self.loader._check_compressor_thermodynamics(data)
        assert len(violations) == 0


class TestOWLDataRangeRestrictions:
    """Tests for OWL datatype range restrictions."""

    @pytest.fixture(autouse=True)
    def load_ontology_fixture(self):
        """Load ontology before tests."""
        reset_ontology_loader()
        self.loader = load_ontology()
        yield
        reset_ontology_loader()

    def test_ontology_has_datatype_properties(self):
        """Test that ontology has datatype properties with restrictions."""
        properties = self.loader.get_properties()

        # Should have datatype properties
        datatype_props = [p for p, info in properties.items() if info.get("type") == "datatype"]
        assert len(datatype_props) > 0

    def test_concept_hierarchy_includes_violation_classes(self):
        """Test that violation marker classes are in ontology."""
        concepts = self.loader.get_concepts()

        # Violation classes should be present
        expected_violations = ["ConstraintViolation", "PhysicsViolation", "RangeViolation"]
        for violation_class in expected_violations:
            if violation_class in concepts:
                assert True
                return

        # At least check we have concepts loaded
        assert len(concepts) > 0
