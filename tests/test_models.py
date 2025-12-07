"""Tests for domain entity models and response models."""

import pytest
from datetime import date, datetime

from logic_guard_layer.models.entities import (
    Component,
    ComponentType,
    Measurement,
    ParsedData,
    MaintenanceEvent,
    EventType,
)
from logic_guard_layer.models.responses import (
    Violation,
    ViolationType,
    ValidationResult,
    ValidationResponse,
    ValidationRequest,
    IterationInfo,
    HealthResponse,
    StatsResponse,
    OntologyUploadRequest,
    OntologyInfoResponse,
    OntologyListResponse,
)


class TestComponentType:
    """Tests for ComponentType enum."""

    def test_motor_value(self):
        """Test Motor component type value."""
        assert ComponentType.MOTOR.value == "Motor"

    def test_pump_value(self):
        """Test Pump component type value."""
        assert ComponentType.PUMP.value == "Pumpe"

    def test_hydraulic_pump_value(self):
        """Test HydraulicPump component type value."""
        assert ComponentType.HYDRAULIC_PUMP.value == "Hydraulikpumpe"

    def test_sensor_value(self):
        """Test Sensor component type value."""
        assert ComponentType.SENSOR.value == "Sensor"

    def test_unknown_value(self):
        """Test Unknown component type value."""
        assert ComponentType.UNKNOWN.value == "Unbekannt"

    def test_enum_from_value(self):
        """Test creating enum from string value."""
        assert ComponentType("Motor") == ComponentType.MOTOR
        assert ComponentType("Pumpe") == ComponentType.PUMP


class TestEventType:
    """Tests for EventType enum."""

    def test_maintenance_value(self):
        """Test Maintenance event type value."""
        assert EventType.MAINTENANCE.value == "Wartung"

    def test_failure_value(self):
        """Test Failure event type value."""
        assert EventType.FAILURE.value == "Ausfall"

    def test_measurement_value(self):
        """Test Measurement event type value."""
        assert EventType.MEASUREMENT.value == "Messung"


class TestMeasurement:
    """Tests for Measurement model."""

    def test_create_measurement(self):
        """Test creating a measurement."""
        m = Measurement(type="Druck", value=250.0, unit="bar")
        assert m.type == "Druck"
        assert m.value == 250.0
        assert m.unit == "bar"

    def test_measurement_to_dict(self):
        """Test measurement serialization."""
        m = Measurement(type="Temperatur", value=75.5, unit="°C")
        data = m.model_dump()
        assert data["type"] == "Temperatur"
        assert data["value"] == 75.5
        assert data["unit"] == "°C"

    def test_measurement_negative_value(self):
        """Test measurement with negative value (allowed)."""
        m = Measurement(type="Temperatur", value=-20.0, unit="°C")
        assert m.value == -20.0


class TestComponent:
    """Tests for Component model."""

    def test_create_component_minimal(self):
        """Test creating a component with minimal fields."""
        c = Component(name="TEST-001")
        assert c.name == "TEST-001"
        assert c.type == ComponentType.UNKNOWN
        assert c.serial_number is None
        assert c.operating_hours is None
        assert c.measurements == []

    def test_create_component_full(self, sample_component):
        """Test creating a component with all fields."""
        assert sample_component.name == "HP-001"
        assert sample_component.type == ComponentType.HYDRAULIC_PUMP
        assert sample_component.serial_number == "SN123456"
        assert sample_component.operating_hours == 5000
        assert sample_component.max_lifespan == 20000
        assert sample_component.maintenance_interval == 2500

    def test_component_with_measurements(self, sample_component_with_measurements):
        """Test component with measurements."""
        assert len(sample_component_with_measurements.measurements) == 1
        assert sample_component_with_measurements.measurements[0].type == "Druck"

    def test_component_german_aliases(self):
        """Test component creation with German aliases."""
        c = Component(
            name="HP-001",
            seriennummer="SN123",
            betriebsstunden=1000,
            max_lebensdauer=5000,
            wartungsintervall=500
        )
        assert c.serial_number == "SN123"
        assert c.operating_hours == 1000
        assert c.max_lifespan == 5000
        assert c.maintenance_interval == 500

    def test_component_populate_by_name(self):
        """Test that populate_by_name is enabled."""
        config = Component.model_config
        assert config.get("populate_by_name") is True

    def test_component_operating_hours_ge_zero(self):
        """Test operating_hours validation (ge=0)."""
        with pytest.raises(ValueError):
            Component(name="TEST", operating_hours=-1)

    def test_component_max_lifespan_gt_zero(self):
        """Test max_lifespan validation (gt=0)."""
        with pytest.raises(ValueError):
            Component(name="TEST", max_lifespan=0)

    def test_component_maintenance_interval_gt_zero(self):
        """Test maintenance_interval validation (gt=0)."""
        with pytest.raises(ValueError):
            Component(name="TEST", maintenance_interval=0)


class TestMaintenanceEvent:
    """Tests for MaintenanceEvent model."""

    def test_create_event_minimal(self):
        """Test creating an event with minimal fields."""
        e = MaintenanceEvent(component_name="HP-001")
        assert e.component_name == "HP-001"
        assert e.event_type == EventType.MAINTENANCE
        assert e.event_date is None
        assert e.description is None
        assert e.technician is None

    def test_create_event_full(self, sample_maintenance_event):
        """Test creating an event with all fields."""
        assert sample_maintenance_event.component_name == "HP-001"
        assert sample_maintenance_event.event_type == EventType.MAINTENANCE
        assert sample_maintenance_event.description == "Regular maintenance"
        assert sample_maintenance_event.technician == "John Doe"

    def test_event_german_aliases(self):
        """Test event creation with German aliases."""
        e = MaintenanceEvent(
            component_name="HP-001",
            datum=date(2024, 1, 15),
            techniker="Max Mustermann"
        )
        assert e.event_date == date(2024, 1, 15)
        assert e.technician == "Max Mustermann"


class TestParsedData:
    """Tests for ParsedData model."""

    def test_create_parsed_data_empty(self):
        """Test creating empty parsed data."""
        pd = ParsedData()
        assert pd.components == []
        assert pd.events == []
        assert pd.raw_values == {}
        assert pd.extraction_confidence == 1.0

    def test_create_parsed_data_with_components(self, sample_parsed_data):
        """Test creating parsed data with components."""
        assert len(sample_parsed_data.components) == 1
        assert sample_parsed_data.components[0].name == "HP-001"
        assert sample_parsed_data.extraction_confidence == 0.95

    def test_get_component_found(self, sample_parsed_data):
        """Test getting a component by name."""
        comp = sample_parsed_data.get_component("HP-001")
        assert comp is not None
        assert comp.name == "HP-001"

    def test_get_component_not_found(self, sample_parsed_data):
        """Test getting a non-existent component."""
        comp = sample_parsed_data.get_component("NONEXISTENT")
        assert comp is None

    def test_extraction_confidence_range(self):
        """Test extraction_confidence bounds."""
        # Valid values
        pd = ParsedData(extraction_confidence=0.0)
        assert pd.extraction_confidence == 0.0

        pd = ParsedData(extraction_confidence=1.0)
        assert pd.extraction_confidence == 1.0

        # Invalid values
        with pytest.raises(ValueError):
            ParsedData(extraction_confidence=-0.1)

        with pytest.raises(ValueError):
            ParsedData(extraction_confidence=1.1)


class TestViolationType:
    """Tests for ViolationType enum."""

    def test_all_types_exist(self):
        """Test all violation types are defined."""
        assert ViolationType.TYPE_ERROR.value == "TYPE_ERROR"
        assert ViolationType.RANGE_ERROR.value == "RANGE_ERROR"
        assert ViolationType.RELATIONAL_ERROR.value == "RELATIONAL_ERROR"
        assert ViolationType.TEMPORAL_ERROR.value == "TEMPORAL_ERROR"
        assert ViolationType.PHYSICAL_ERROR.value == "PHYSICAL_ERROR"
        assert ViolationType.PARSE_ERROR.value == "PARSE_ERROR"
        assert ViolationType.UNKNOWN_ERROR.value == "UNKNOWN_ERROR"


class TestViolation:
    """Tests for Violation model."""

    def test_create_violation(self, sample_violation):
        """Test creating a violation."""
        assert sample_violation.type == ViolationType.RANGE_ERROR
        assert sample_violation.constraint == "operating_hours >= 0"
        assert "negative" in sample_violation.message.lower()
        assert sample_violation.entity == "HP-001"
        assert sample_violation.property_name == "operating_hours"
        assert sample_violation.actual_value == -100
        assert sample_violation.expected_value == ">= 0"
        assert sample_violation.severity == "error"

    def test_violation_str(self, sample_violation):
        """Test violation string representation."""
        s = str(sample_violation)
        assert "RANGE_ERROR" in s
        assert "negative" in s.lower()

    def test_violation_default_severity(self):
        """Test default severity is 'error'."""
        v = Violation(
            type=ViolationType.RANGE_ERROR,
            constraint="test",
            message="test message"
        )
        assert v.severity == "error"


class TestIterationInfo:
    """Tests for IterationInfo model."""

    def test_create_iteration_info(self):
        """Test creating iteration info."""
        info = IterationInfo(
            number=1,
            violations_count=3,
            corrected_text="Corrected text"
        )
        assert info.number == 1
        assert info.violations_count == 3
        assert info.corrected_text == "Corrected text"

    def test_iteration_info_no_text(self):
        """Test iteration info without corrected text."""
        info = IterationInfo(number=2, violations_count=0)
        assert info.corrected_text is None


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_create_success_result(self, sample_validation_result_success):
        """Test creating a successful validation result."""
        assert sample_validation_result_success.success is True
        assert sample_validation_result_success.violations == []
        assert sample_validation_result_success.violations_count == 0

    def test_create_failure_result(self, sample_validation_result_failure):
        """Test creating a failed validation result."""
        assert sample_validation_result_failure.success is False
        assert len(sample_validation_result_failure.violations) == 1
        assert sample_validation_result_failure.violations_count == 1

    def test_to_summary_success(self, sample_validation_result_success):
        """Test summary for successful validation."""
        summary = sample_validation_result_success.to_summary()
        assert "PASSED" in summary
        assert "1 iteration" in summary

    def test_to_summary_failure(self, sample_validation_result_failure):
        """Test summary for failed validation."""
        summary = sample_validation_result_failure.to_summary()
        assert "FAILED" in summary
        assert "1 violation" in summary

    def test_violations_count_property(self, sample_validation_result_failure):
        """Test violations_count property."""
        assert sample_validation_result_failure.violations_count == len(
            sample_validation_result_failure.violations
        )


class TestValidationRequest:
    """Tests for ValidationRequest model."""

    def test_create_request_minimal(self):
        """Test creating a request with minimal fields."""
        req = ValidationRequest(text="Test text")
        assert req.text == "Test text"
        assert req.schema_name == "maintenance"
        assert req.auto_correct is True
        assert req.max_iterations is None

    def test_create_request_full(self):
        """Test creating a request with all fields."""
        req = ValidationRequest(
            text="Test text",
            schema_name="custom",
            max_iterations=3,
            auto_correct=False
        )
        assert req.schema_name == "custom"
        assert req.max_iterations == 3
        assert req.auto_correct is False

    def test_request_text_min_length(self):
        """Test text minimum length validation."""
        with pytest.raises(ValueError):
            ValidationRequest(text="")

    def test_request_max_iterations_range(self):
        """Test max_iterations range validation."""
        # Valid
        req = ValidationRequest(text="test", max_iterations=1)
        assert req.max_iterations == 1

        req = ValidationRequest(text="test", max_iterations=10)
        assert req.max_iterations == 10

        # Invalid
        with pytest.raises(ValueError):
            ValidationRequest(text="test", max_iterations=0)

        with pytest.raises(ValueError):
            ValidationRequest(text="test", max_iterations=11)


class TestValidationResponse:
    """Tests for ValidationResponse model."""

    def test_create_response(self):
        """Test creating a validation response."""
        resp = ValidationResponse(
            success=True,
            data={"name": "HP-001"},
            violations=[],
            iterations=1,
            checked_constraints=8,
            processing_time_ms=100.0,
            confidence=0.95
        )
        assert resp.success is True
        assert resp.data == {"name": "HP-001"}
        assert resp.iterations == 1

    def test_from_result(self, sample_validation_result_success):
        """Test creating response from ValidationResult."""
        resp = ValidationResponse.from_result(sample_validation_result_success)
        assert resp.success == sample_validation_result_success.success
        assert resp.iterations == sample_validation_result_success.iterations
        assert resp.confidence == sample_validation_result_success.confidence


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_create_health_response(self):
        """Test creating a health response."""
        resp = HealthResponse(
            status="healthy",
            version="1.0.0",
            model="test-model",
            ontology_loaded=True
        )
        assert resp.status == "healthy"
        assert resp.version == "1.0.0"
        assert resp.ontology_loaded is True


class TestStatsResponse:
    """Tests for StatsResponse model."""

    def test_create_stats_response(self):
        """Test creating a stats response."""
        resp = StatsResponse(
            total_validations=100,
            successful_validations=90,
            failed_validations=10,
            success_rate=0.9,
            avg_iterations=1.5,
            avg_processing_time_ms=150.0,
            constraints_count=8
        )
        assert resp.total_validations == 100
        assert resp.success_rate == 0.9

    def test_stats_response_defaults(self):
        """Test stats response defaults."""
        resp = StatsResponse()
        assert resp.total_validations == 0
        assert resp.success_rate == 0.0


class TestOntologyUploadRequest:
    """Tests for OntologyUploadRequest model."""

    def test_create_upload_request(self, valid_ontology_schema):
        """Test creating an ontology upload request."""
        req = OntologyUploadRequest(
            name="test-ontology",
            description="Test description",
            schema=valid_ontology_schema
        )
        assert req.name == "test-ontology"
        assert req.description == "Test description"
        assert req.ontology_schema == valid_ontology_schema

    def test_upload_request_name_validation(self, valid_ontology_schema):
        """Test name validation."""
        with pytest.raises(ValueError):
            OntologyUploadRequest(name="", schema=valid_ontology_schema)


class TestOntologyInfoResponse:
    """Tests for OntologyInfoResponse model."""

    def test_create_info_response(self):
        """Test creating an ontology info response."""
        resp = OntologyInfoResponse(
            name="maintenance",
            description="Default ontology",
            version="1.0.0",
            created_at=datetime.now(),
            concepts_count=5,
            constraints_count=8,
            is_default=True,
            is_active=True
        )
        assert resp.name == "maintenance"
        assert resp.is_default is True
        assert resp.is_active is True


class TestOntologyListResponse:
    """Tests for OntologyListResponse model."""

    def test_create_list_response(self):
        """Test creating an ontology list response."""
        info = OntologyInfoResponse(
            name="maintenance",
            description="Default",
            version="1.0.0",
            created_at=datetime.now(),
            concepts_count=5,
            constraints_count=8,
            is_default=True
        )
        resp = OntologyListResponse(
            ontologies=[info],
            active="maintenance"
        )
        assert len(resp.ontologies) == 1
        assert resp.active == "maintenance"
